class CompleteTestEnvironment:
    """Provides a complete set of application environment variables for tests."""

    @staticmethod
    def application_variables() -> dict[str, str]:
        """Return default environment variables required by the application."""
        return {
            "APP_MODE": "PROD",
            "LOG_LEVEL": "INFO",
            "LOG_RETENTION_DAYS": "14",
            "SILVINA_APP_NAME": "Silvina Editorial Assistant",
            "OLLAMA_MODEL_NAME": "gemma4-26b-adapted",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_THINK": "false",
            "OLLAMA_MODEL_KEEP_ALIVE": "15m",
            "OLLAMA_WARMUP_ON_STARTUP": "true",
            "USE_EXTERNAL_LLM": "false",
            "EXTERNAL_LLM_THINK": "false",
        }
