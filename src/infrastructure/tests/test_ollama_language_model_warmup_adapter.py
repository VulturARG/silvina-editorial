from http import HTTPStatus
from unittest import TestCase
from unittest.mock import patch

from ollama import RequestError, ResponseError

from src.domain.exceptions.language_model_errors import (
    LanguageModelLoadFailed,
    LanguageModelNotFound,
    LanguageModelUnavailable,
)
from src.domain.language_model.language_model_warmup_port import LanguageModelWarmupPort
from src.infrastructure.adapters.llm_generator.ollama_backend_error_mapper import (
    OllamaBackendErrorMapper,
)
from src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter import (
    OllamaLanguageModelWarmupAdapter,
)


class TestOllamaLanguageModelWarmupAdapter(TestCase):
    def setUp(self) -> None:
        self.model_name = "hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS"
        self.base_url = "http://localhost:11434"
        self.keep_alive = "15m"
        self.error_mapper = OllamaBackendErrorMapper()
        self.adapter = OllamaLanguageModelWarmupAdapter(
            model_name=self.model_name,
            base_url=self.base_url,
            keep_alive=self.keep_alive,
            error_mapper=self.error_mapper,
        )

    def test_implements_language_model_warmup_port(self):
        self.assertIsInstance(self.adapter, LanguageModelWarmupPort)

    @patch(
        "src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter.ollama.Client"
    )
    def test_warm_up_calls_client_generate_with_empty_prompt_and_keep_alive(
        self, mock_client_class
    ):
        mock_client = mock_client_class.return_value

        self.adapter.warm_up()

        mock_client_class.assert_called_once_with(host=self.base_url)
        mock_client.generate.assert_called_once_with(
            model=self.model_name,
            prompt="",
            keep_alive=self.keep_alive,
        )

    @patch(
        "src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter.ollama.Client"
    )
    def test_warm_up_raises_language_model_not_found_on_404_response_error(self, mock_client_class):
        mock_client = mock_client_class.return_value
        backend_error = ResponseError("model not found", HTTPStatus.NOT_FOUND.value)
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelNotFound) as context:
            self.adapter.warm_up()

        self.assertIs(context.exception.__cause__, backend_error)

    @patch(
        "src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter.ollama.Client"
    )
    def test_warm_up_raises_language_model_load_failed_on_500_response_error(
        self, mock_client_class
    ):
        mock_client = mock_client_class.return_value
        backend_error = ResponseError(
            "llama-server startup failed: out-of-memory",
            HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelLoadFailed) as context:
            self.adapter.warm_up()

        self.assertIs(context.exception.__cause__, backend_error)

    @patch(
        "src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter.ollama.Client"
    )
    def test_warm_up_raises_language_model_load_failed_on_503_response_error(
        self, mock_client_class
    ):
        mock_client = mock_client_class.return_value
        backend_error = ResponseError(
            "service overloaded",
            HTTPStatus.SERVICE_UNAVAILABLE.value,
        )
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelLoadFailed) as context:
            self.adapter.warm_up()

        self.assertIs(context.exception.__cause__, backend_error)

    @patch(
        "src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter.ollama.Client"
    )
    def test_warm_up_raises_language_model_unavailable_on_connection_error(self, mock_client_class):
        mock_client = mock_client_class.return_value
        backend_error = ConnectionError("backend unreachable")
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.warm_up()

        self.assertIs(context.exception.__cause__, backend_error)

    @patch(
        "src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter.ollama.Client"
    )
    def test_warm_up_raises_language_model_unavailable_on_request_error(self, mock_client_class):
        mock_client = mock_client_class.return_value
        backend_error = RequestError("request timeout")
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.warm_up()

        self.assertIs(context.exception.__cause__, backend_error)
