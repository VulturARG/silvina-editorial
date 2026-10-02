from http import HTTPStatus
from unittest import TestCase
from unittest.mock import patch

from ollama import RequestError, ResponseError

from src.domain.exceptions.language_model_errors import (
    LanguageModelLoadFailed,
    LanguageModelNotFound,
    LanguageModelUnavailable,
)
from src.infrastructure.adapters.llm_generator.ollama_generator_adapter import (
    OllamaGeneratorAdapter,
)


class TestOllamaGeneratorAdapter(TestCase):
    """Unit tests for the OllamaGeneratorAdapter class."""

    def setUp(self) -> None:
        self.model_name = "hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS"
        self.base_url = "http://localhost:11434"
        self.sample_prompt = "prompt"
        self.sample_options = {"temperature": 0.1, "num_predict": 300}
        self.adapter = OllamaGeneratorAdapter(
            model_name=self.model_name,
            base_url=self.base_url,
            think=False,
        )

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_returns_stripped_response_text(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": "  some text  "}

        result = self.adapter.generate(prompt=self.sample_prompt)

        self.assertEqual(result, "some text")

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_raises_language_model_unavailable_on_backend_failure(self, mock_client_class):
        mock_client = mock_client_class.return_value
        backend_error = ConnectionError("backend unreachable")
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_raises_language_model_not_found_on_404_response_error(
        self, mock_client_class
    ):
        mock_client = mock_client_class.return_value
        backend_error = ResponseError("model not found", HTTPStatus.NOT_FOUND.value)
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelNotFound) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_raises_language_model_load_failed_on_500_response_error(
        self, mock_client_class
    ):
        mock_client = mock_client_class.return_value
        backend_error = ResponseError(
            "llama-server startup failed: out-of-memory",
            HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelLoadFailed) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_raises_language_model_load_failed_on_503_response_error(
        self, mock_client_class
    ):
        mock_client = mock_client_class.return_value
        backend_error = ResponseError(
            "service overloaded",
            HTTPStatus.SERVICE_UNAVAILABLE.value,
        )
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelLoadFailed) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_raises_language_model_unavailable_on_400_response_error(
        self, mock_client_class
    ):
        mock_client = mock_client_class.return_value
        backend_error = ResponseError("bad request", HTTPStatus.BAD_REQUEST.value)
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_raises_language_model_unavailable_on_request_error(self, mock_client_class):
        mock_client = mock_client_class.return_value
        backend_error = RequestError("request timeout")
        mock_client.generate.side_effect = backend_error

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_instantiates_client_with_configured_base_url(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": "some text"}

        self.adapter.generate(prompt=self.sample_prompt)

        mock_client_class.assert_called_once_with(host=self.base_url)

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_forwards_options_dict_to_ollama_generate(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": "some text"}

        self.adapter.generate(prompt=self.sample_prompt, options=self.sample_options)

        mock_client.generate.assert_called_once_with(
            model=self.model_name,
            prompt=self.sample_prompt,
            options=self.sample_options,
            think=False,
        )

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_without_options_argument_preserves_prior_behavior(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": "some text"}

        self.adapter.generate(prompt=self.sample_prompt)

        mock_client.generate.assert_called_once_with(
            model=self.model_name,
            prompt=self.sample_prompt,
            options=None,
            think=False,
        )

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_sends_configured_think_false_with_options(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": "some text"}

        self.adapter.generate(prompt=self.sample_prompt, options=self.sample_options)

        mock_client.generate.assert_called_once_with(
            model=self.model_name,
            prompt=self.sample_prompt,
            options=self.sample_options,
            think=False,
        )

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_sends_configured_think_false_without_options(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": "some text"}

        self.adapter.generate(prompt=self.sample_prompt)

        mock_client.generate.assert_called_once_with(
            model=self.model_name,
            prompt=self.sample_prompt,
            options=None,
            think=False,
        )

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_sends_configured_think_true_with_options(self, mock_client_class):
        adapter_with_thinking = OllamaGeneratorAdapter(
            model_name=self.model_name,
            base_url=self.base_url,
            think=True,
        )
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": "some text"}

        adapter_with_thinking.generate(prompt=self.sample_prompt, options=self.sample_options)

        mock_client.generate.assert_called_once_with(
            model=self.model_name,
            prompt=self.sample_prompt,
            options=self.sample_options,
            think=True,
        )

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_sends_configured_think_true_without_options(self, mock_client_class):
        adapter_with_thinking = OllamaGeneratorAdapter(
            model_name=self.model_name,
            base_url=self.base_url,
            think=True,
        )
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": "some text"}

        adapter_with_thinking.generate(prompt=self.sample_prompt)

        mock_client.generate.assert_called_once_with(
            model=self.model_name,
            prompt=self.sample_prompt,
            options=None,
            think=True,
        )

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_returns_empty_string_when_response_text_is_empty(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {"response": ""}

        result = self.adapter.generate(prompt=self.sample_prompt)

        self.assertEqual(result, "")

    @patch("src.infrastructure.adapters.llm_generator.ollama_generator_adapter.ollama.Client")
    def test_generate_reads_only_response_field_ignoring_thinking_field(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.generate.return_value = {
            "response": "answer",
            "thinking": "internal reasoning",
        }

        result = self.adapter.generate(prompt=self.sample_prompt)

        self.assertEqual(result, "answer")
