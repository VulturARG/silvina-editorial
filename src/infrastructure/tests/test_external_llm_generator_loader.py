from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.domain.enums.ai_provider import AiProvider
from src.domain.exceptions.language_model_errors import LanguageModelBackendNotInstalled
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.infrastructure.wirings.external_llm_generator_loader import (
    ExternalLlmGeneratorLoader,
)


class TestExternalLlmGeneratorLoader(TestCase):
    def test_load_resolves_and_instantiates_registered_adapter(self):
        mock_adapter_instance = MagicMock(spec=LlmGeneratorPort)
        mock_adapter_class = MagicMock(return_value=mock_adapter_instance)
        mock_module = MagicMock()
        mock_module.ClaudeGeneratorAdapter = mock_adapter_class

        with patch(
            "src.infrastructure.wirings.external_llm_generator_loader.import_module",
            return_value=mock_module,
        ) as mock_import_module:
            loader = ExternalLlmGeneratorLoader()
            generator = loader.load(
                provider=AiProvider.CLAUDE,
                model_name="claude-3-7-sonnet",
            )

        mock_import_module.assert_called_once_with(
            "src.infrastructure.adapters.llm_generator.claude_generator_adapter"
        )
        mock_adapter_class.assert_called_once_with(model_name="claude-3-7-sonnet")
        self.assertIs(generator, mock_adapter_instance)

    def test_load_uses_custom_registry_when_provided(self):
        mock_adapter_instance = MagicMock(spec=LlmGeneratorPort)
        mock_adapter_class = MagicMock(return_value=mock_adapter_instance)
        mock_module = MagicMock()
        mock_module.CustomAdapter = mock_adapter_class

        custom_registry = {
            AiProvider.CLAUDE: (
                "custom.module.path",
                "CustomAdapter",
            )
        }

        with patch(
            "src.infrastructure.wirings.external_llm_generator_loader.import_module",
            return_value=mock_module,
        ) as mock_import_module:
            loader = ExternalLlmGeneratorLoader(registry=custom_registry)
            generator = loader.load(
                provider=AiProvider.CLAUDE,
                model_name="custom-model",
            )

        mock_import_module.assert_called_once_with("custom.module.path")
        mock_adapter_class.assert_called_once_with(model_name="custom-model")
        self.assertIs(generator, mock_adapter_instance)

    def test_load_raises_language_model_backend_not_installed_when_module_not_found(self):
        with patch(
            "src.infrastructure.wirings.external_llm_generator_loader.import_module",
            side_effect=ModuleNotFoundError("No module named 'claude_agent_sdk'"),
        ):
            loader = ExternalLlmGeneratorLoader()
            with self.assertRaises(LanguageModelBackendNotInstalled) as context:
                loader.load(
                    provider=AiProvider.CLAUDE,
                    model_name="claude-3-7-sonnet",
                )

        self.assertIsInstance(context.exception.__cause__, ModuleNotFoundError)

    def test_load_raises_value_error_for_unknown_provider(self):
        loader = ExternalLlmGeneratorLoader()
        with self.assertRaises(ValueError) as context:
            loader.load(
                provider=AiProvider.OLLAMA,
                model_name="ollama-model",
            )

        self.assertIn("ollama", str(context.exception))
