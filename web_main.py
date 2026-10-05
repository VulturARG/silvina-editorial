"""Root launcher for Silvina Editorial Assistant web interface."""

import uvicorn

from src.infrastructure.fastapi.fastapi_app import app
from src.infrastructure.fastapi.src.config.dependencies import (
    get_warm_up_language_model_use_case,
)
from src.infrastructure.fastapi.src.utils.language_model_warm_up_starter import (
    LanguageModelWarmUpStarter,
)
from src.infrastructure.wirings.logging_config_wiring import LoggingConfigWiring


def main() -> None:
    """Run the FastAPI web application server on localhost."""
    LoggingConfigWiring().create_logging_config().configure()
    LanguageModelWarmUpStarter(get_warm_up_language_model_use_case()).start()
    uvicorn.run(app, host="127.0.0.1", port=7861)


if __name__ == "__main__":
    main()
