from unittest import TestCase

from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)


class TestCompleteTestEnvironment(TestCase):
    """Tests for CompleteTestEnvironment."""

    def test_application_variables_returns_expected_default_values(self) -> None:
        expected_variables = {
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
        self.assertEqual(CompleteTestEnvironment.application_variables(), expected_variables)

    def test_application_variables_returns_new_dictionary_instance(self) -> None:
        first_variables = CompleteTestEnvironment.application_variables()
        second_variables = CompleteTestEnvironment.application_variables()
        self.assertIsNot(first_variables, second_variables)

        first_variables["APP_MODE"] = "DEBUG"
        self.assertEqual(CompleteTestEnvironment.application_variables()["APP_MODE"], "PROD")
