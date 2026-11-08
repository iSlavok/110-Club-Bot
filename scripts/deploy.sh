#!/usr/bin/env bash
# Deploys tag vX.Y.Z without GitHub Actions: builds both images here and loads them on the server over SSH.
# Server: DEPLOY_SSH (ssh destination or ~/.ssh/config alias) and DEPLOY_PATH, from the environment or .env.deploy.
set -euo pipefail

VERSION="${1:-}"
# The names docker-compose.yml runs and the release workflow publishes: change them together.
IMAGE_PREFIX="ghcr.io/islavok/110-club-bot"

[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]] || { echo "usage: $0 X.Y.Z" >&2; exit 1; }
TAG="v$VERSION"

cd "$(dirname "$0")/.."
# Gitignored by the .env.* rule: the server address and path stay out of the public repo.
if [[ -f .env.deploy ]]; then
  source .env.deploy
fi
: "${DEPLOY_SSH:?set DEPLOY_SSH in .env.deploy}" "${DEPLOY_PATH:?set DEPLOY_PATH in .env.deploy}"
REVISION="$(git rev-parse -q --verify "refs/tags/$TAG^{commit}")" || { echo "No tag $TAG: git fetch --tags" >&2; exit 1; }

ARCH="$(ssh "$DEPLOY_SSH" uname -m)"
case "$ARCH" in
  x86_64) PLATFORM=linux/amd64 ;;
  aarch64 | arm64) PLATFORM=linux/arm64 ;;
  *) echo "Unsupported server architecture $ARCH" >&2; exit 1 ;;
esac

read -r -p "Deploy $TAG ($PLATFORM) to $DEPLOY_SSH:$DEPLOY_PATH? [y/N] " answer
[[ "$answer" == y ]] || exit 1

# A clean checkout of the tag, so uncommitted changes never reach the images.
WORKTREE="$(mktemp -d)"
trap 'git worktree remove --force "$WORKTREE" 2>/dev/null || rm -rf "$WORKTREE"' EXIT
git worktree add --detach --quiet "$WORKTREE" "$TAG"

IMAGES=()
for image in backend web; do
  name="$IMAGE_PREFIX-$image:$VERSION"
  docker buildx build \
    --platform "$PLATFORM" \
    --load \
    --label "org.opencontainers.image.version=$VERSION" \
    --label "org.opencontainers.image.revision=$REVISION" \
    --file "$WORKTREE/docker/$image.Dockerfile" \
    --tag "$name" \
    "$WORKTREE"
  IMAGES+=("$name")
done

echo "Uploading ${IMAGES[*]}"
docker save --platform "$PLATFORM" "${IMAGES[@]}" | gzip | ssh "$DEPLOY_SSH" 'gunzip | docker load'

REMOTE_PATH="$(printf %q "$DEPLOY_PATH")"
# The compose file of the deployed version, so a rollback also rolls back the topology.
ssh "$DEPLOY_SSH" "cat > $REMOTE_PATH/docker-compose.yml" < "$WORKTREE/docker-compose.yml"

# Same steps as the deploy workflow, but the images are already on the server: never pull them.
# IMAGE_TAG goes to .env only after the stack is healthy, so a manual `docker compose up` keeps the last good one.
ssh "$DEPLOY_SSH" "IMAGE_TAG=$VERSION DEPLOY_PATH=$REMOTE_PATH bash -s" <<'EOF'
set -eu
cd "$DEPLOY_PATH"
export IMAGE_TAG
docker compose up -d --wait --wait-timeout 300 --remove-orphans --pull never
sed -i '/^IMAGE_TAG=/d' .env
echo "IMAGE_TAG=$IMAGE_TAG" >> .env
docker image prune -f
docker compose ps
EOF
