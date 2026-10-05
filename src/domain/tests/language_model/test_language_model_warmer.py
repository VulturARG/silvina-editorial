from unittest import TestCase

from src.domain.exceptions.language_model_errors import LanguageModelUnavailable
from src.domain.language_model.language_model_warmer import LanguageModelWarmer
from src.domain.tests.language_model.fake_language_model_warmup_port import (
    FakeLanguageModelWarmupPort,
)


class TestLanguageModelWarmer(TestCase):
    def test_warm_up_delegates_to_port_once(self):
        fake_port = FakeLanguageModelWarmupPort()
        warmer = LanguageModelWarmer(language_model_warmup_port=fake_port)

        warmer.warm_up()

        self.assertEqual(fake_port.warm_up_call_count, 1)

    def test_warm_up_logs_duration_at_info_level_on_success(self):
        fake_port = FakeLanguageModelWarmupPort()
        warmer = LanguageModelWarmer(language_model_warmup_port=fake_port)

        with self.assertLogs(
            "src.domain.language_model.language_model_warmer", level="INFO"
        ) as captured_logs:
            warmer.warm_up()

        self.assertEqual(len(captured_logs.records), 1)
        self.assertEqual(captured_logs.records[0].levelname, "INFO")
        self.assertIn("Language model warm-up completed in", captured_logs.output[0])

    def test_warm_up_propagates_language_model_unavailable_unchanged(self):
        fake_port = FakeLanguageModelWarmupPort(raise_error=LanguageModelUnavailable())
        warmer = LanguageModelWarmer(language_model_warmup_port=fake_port)

        with self.assertRaises(LanguageModelUnavailable):
            warmer.warm_up()

        self.assertEqual(fake_port.warm_up_call_count, 1)

    def test_warm_up_logs_nothing_on_failure(self):
        fake_port = FakeLanguageModelWarmupPort(raise_error=LanguageModelUnavailable())
        warmer = LanguageModelWarmer(language_model_warmup_port=fake_port)

        with self.assertNoLogs("src.domain.language_model.language_model_warmer", level="INFO"):
            with self.assertRaises(LanguageModelUnavailable):
                warmer.warm_up()
