"""Root launcher for Silvina Editorial Assistant web interface."""

import uvicorn

from src.infrastructure.fastapi.fastapi_app import app


def main() -> None:
    """Run the FastAPI web application server on localhost."""
    uvicorn.run(app, host="127.0.0.1", port=7861)


if __name__ == "__main__":
    main()
