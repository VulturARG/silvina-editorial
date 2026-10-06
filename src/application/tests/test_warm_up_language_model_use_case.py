from unittest import TestCase

from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.domain.exceptions.base_src_error import SrcGenericError
from src.domain.exceptions.language_model_errors import LanguageModelUnavailable
from src.domain.language_model.language_model_warmer import LanguageModelWarmer
from src.domain.tests.language_model.fake_language_model_warmup_port import (
    FakeLanguageModelWarmupPort,
)


class TestWarmUpLanguageModelUseCase(TestCase):
    def test_execute_calls_warmer_once(self):
        fake_port = FakeLanguageModelWarmupPort()
        warmer = LanguageModelWarmer(language_model_warmup_port=fake_port)
        use_case = WarmUpLanguageModelUseCase(language_model_warmer=warmer)

        use_case.execute()

        self.assertEqual(fake_port.warm_up_call_count, 1)

    def test_execute_propagates_language_model_unavailable_as_is(self):
        fake_port = FakeLanguageModelWarmupPort(raise_error=LanguageModelUnavailable())
        warmer = LanguageModelWarmer(language_model_warmup_port=fake_port)
        use_case = WarmUpLanguageModelUseCase(language_model_warmer=warmer)

        with self.assertRaises(LanguageModelUnavailable):
            use_case.execute()

    def test_execute_wraps_unexpected_runtime_error_in_src_generic_error(self):
        fake_port = FakeLanguageModelWarmupPort(raise_error=RuntimeError("unexpected failure"))
        warmer = LanguageModelWarmer(language_model_warmup_port=fake_port)
        use_case = WarmUpLanguageModelUseCase(language_model_warmer=warmer)

        with self.assertRaises(SrcGenericError):
            use_case.execute()
