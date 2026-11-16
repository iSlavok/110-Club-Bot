FROM python:3.13-slim AS builder
# uv fetches git dependencies with the git CLI; the runtime stage gets only /app.
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
# The platform client is a private package: PLATFORM_CLIENT=on installs it with a token that can read it.
# A build arg, not the secret, decides: BuildKit leaves secrets out of the cache key, so a cached layer
# without the client would silently serve a build with the token. The token reaches git through env for
# this one RUN and stays out of the layers and the git config.
ARG PLATFORM_CLIENT=off
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=secret,id=platform_client_token,required=false \
    if [ "$PLATFORM_CLIENT" = on ]; then \
      [ -s /run/secrets/platform_client_token ] || { echo "PLATFORM_CLIENT=on needs the platform_client_token secret" >&2; exit 1; }; \
      GIT_CONFIG_COUNT=1 \
      GIT_CONFIG_KEY_0="url.https://x-access-token:$(cat /run/secrets/platform_client_token)@github.com/.insteadOf" \
      GIT_CONFIG_VALUE_0="https://github.com/" \
      uv sync --frozen --no-default-groups --group platform --no-install-project; \
    else \
      uv sync --frozen --no-default-groups --no-install-project; \
    fi
COPY backend/ ./

FROM python:3.13-slim
RUN useradd --system --uid 10001 --no-create-home app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/livez')"]
CMD ["python", "main.py"]
