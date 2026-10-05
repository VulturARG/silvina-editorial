from http import HTTPStatus
from unittest import TestCase

from ollama import RequestError, ResponseError

from src.domain.exceptions.language_model_errors import (
    LanguageModelLoadFailed,
    LanguageModelNotFound,
    LanguageModelUnavailable,
)
from src.infrastructure.adapters.llm_generator.ollama_backend_error_mapper import (
    OllamaBackendErrorMapper,
)


class TestOllamaBackendErrorMapper(TestCase):
    def setUp(self) -> None:
        self.mapper = OllamaBackendErrorMapper()

    def test_maps_404_response_error_to_language_model_not_found(self):
        backend_error = ResponseError("model not found", HTTPStatus.NOT_FOUND.value)
        result = self.mapper.map(backend_error)
        self.assertIsInstance(result, LanguageModelNotFound)

    def test_maps_500_response_error_to_language_model_load_failed(self):
        backend_error = ResponseError(
            "internal server error",
            HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )
        result = self.mapper.map(backend_error)
        self.assertIsInstance(result, LanguageModelLoadFailed)

    def test_maps_503_response_error_to_language_model_load_failed(self):
        backend_error = ResponseError(
            "service unavailable",
            HTTPStatus.SERVICE_UNAVAILABLE.value,
        )
        result = self.mapper.map(backend_error)
        self.assertIsInstance(result, LanguageModelLoadFailed)

    def test_maps_400_response_error_to_language_model_unavailable(self):
        backend_error = ResponseError("bad request", HTTPStatus.BAD_REQUEST.value)
        result = self.mapper.map(backend_error)
        self.assertIsInstance(result, LanguageModelUnavailable)

    def test_maps_request_error_to_language_model_unavailable(self):
        backend_error = RequestError("connection timeout")
        result = self.mapper.map(backend_error)
        self.assertIsInstance(result, LanguageModelUnavailable)

    def test_maps_connection_error_to_language_model_unavailable(self):
        backend_error = ConnectionError("backend unreachable")
        result = self.mapper.map(backend_error)
        self.assertIsInstance(result, LanguageModelUnavailable)

    def test_maps_arbitrary_exception_to_language_model_unavailable(self):
        backend_error = RuntimeError("unexpected runtime failure")
        result = self.mapper.map(backend_error)
        self.assertIsInstance(result, LanguageModelUnavailable)

    def test_maps_response_error_with_none_status_code_to_language_model_unavailable(self):
        backend_error = ResponseError("error without status code")
        result = self.mapper.map(backend_error)
        self.assertIsInstance(result, LanguageModelUnavailable)
