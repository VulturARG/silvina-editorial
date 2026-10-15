from unittest import TestCase

from src.application.ensure_language_model_server_use_case import (
    EnsureLanguageModelServerUseCase,
)
from src.domain.exceptions.base_src_error import SrcGenericError
from src.domain.exceptions.language_model_errors import LanguageModelServerStartFailed
from src.domain.language_model.language_model_server_starter import (
    LanguageModelServerStarter,
)
from src.domain.tests.language_model.fake_language_model_server_port import (
    FakeLanguageModelServerPort,
)


class TestEnsureLanguageModelServerUseCase(TestCase):
    def test_execute_calls_starter_once(self):
        fake_port = FakeLanguageModelServerPort(is_running_result=False)
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)
        use_case = EnsureLanguageModelServerUseCase(language_model_server_starter=starter)

        use_case.execute()

        self.assertEqual(fake_port.start_call_count, 1)

    def test_execute_propagates_language_model_server_start_failed_as_is(self):
        fake_port = FakeLanguageModelServerPort(
            is_running_result=False,
            raise_error_on_start=LanguageModelServerStartFailed(),
        )
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)
        use_case = EnsureLanguageModelServerUseCase(language_model_server_starter=starter)

        with self.assertRaises(LanguageModelServerStartFailed):
            use_case.execute()

    def test_execute_wraps_unexpected_runtime_error_in_src_generic_error(self):
        fake_port = FakeLanguageModelServerPort(
            is_running_result=False,
            raise_error_on_start=RuntimeError("unexpected failure"),
        )
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)
        use_case = EnsureLanguageModelServerUseCase(language_model_server_starter=starter)

        with self.assertRaises(SrcGenericError):
            use_case.execute()
