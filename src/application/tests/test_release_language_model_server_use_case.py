from unittest import TestCase

from src.application.release_language_model_server_use_case import (
    ReleaseLanguageModelServerUseCase,
)
from src.domain.exceptions.base_src_error import SrcGenericError
from src.domain.language_model.language_model_server_starter import (
    LanguageModelServerStarter,
)
from src.domain.tests.language_model.fake_language_model_server_port import (
    FakeLanguageModelServerPort,
)


class TestReleaseLanguageModelServerUseCase(TestCase):
    def test_execute_calls_release_on_starter(self):
        fake_port = FakeLanguageModelServerPort()
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)
        use_case = ReleaseLanguageModelServerUseCase(language_model_server_starter=starter)

        use_case.execute()

        self.assertEqual(fake_port.mark_idle_call_count, 1)

    def test_execute_wraps_unexpected_runtime_error_in_src_generic_error(self):
        fake_port = FakeLanguageModelServerPort(
            raise_error_on_mark_idle=RuntimeError("unexpected failure")
        )
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)
        use_case = ReleaseLanguageModelServerUseCase(language_model_server_starter=starter)

        with self.assertRaises(SrcGenericError):
            use_case.execute()
