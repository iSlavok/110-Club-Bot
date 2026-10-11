import json
import sys

from dishka import make_async_container

from api.app import create_app


# The schema is built from routes only, so an empty container is enough and no settings or services are needed.
def main() -> None:
    schema = create_app(make_async_container()).openapi()
    sys.stdout.write(json.dumps(schema, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
