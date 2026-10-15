from unittest import TestCase

from src.domain.exceptions.language_model_errors import LanguageModelServerStartFailed
from src.domain.language_model.language_model_server_starter import (
    LanguageModelServerStarter,
)
from src.domain.tests.language_model.fake_language_model_server_port import (
    FakeLanguageModelServerPort,
)


class TestLanguageModelServerStarter(TestCase):
    def test_ensure_running_does_not_start_when_server_already_running(self):
        fake_port = FakeLanguageModelServerPort(is_running_result=True)
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        starter.ensure_running()

        self.assertEqual(fake_port.is_running_call_count, 1)
        self.assertEqual(fake_port.start_call_count, 0)

    def test_ensure_running_does_not_log_when_server_already_running(self):
        fake_port = FakeLanguageModelServerPort(is_running_result=True)
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        with self.assertNoLogs(
            "src.domain.language_model.language_model_server_starter", level="INFO"
        ):
            starter.ensure_running()

    def test_ensure_running_starts_server_when_not_running(self):
        fake_port = FakeLanguageModelServerPort(is_running_result=False)
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        starter.ensure_running()

        self.assertEqual(fake_port.is_running_call_count, 1)
        self.assertEqual(fake_port.start_call_count, 1)

    def test_ensure_running_logs_start_attempt_and_duration_on_success(self):
        fake_port = FakeLanguageModelServerPort(is_running_result=False)
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        with self.assertLogs(
            "src.domain.language_model.language_model_server_starter", level="INFO"
        ) as captured_logs:
            starter.ensure_running()

        self.assertEqual(len(captured_logs.records), 2)
        self.assertIn("starting", captured_logs.output[0].lower())
        self.assertIn("Language model server started in", captured_logs.output[1])

    def test_ensure_running_propagates_start_failure_unchanged(self):
        fake_port = FakeLanguageModelServerPort(
            is_running_result=False,
            raise_error_on_start=LanguageModelServerStartFailed(),
        )
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        with self.assertRaises(LanguageModelServerStartFailed):
            starter.ensure_running()

        self.assertEqual(fake_port.start_call_count, 1)

    def test_ensure_running_does_not_log_completion_on_start_failure(self):
        fake_port = FakeLanguageModelServerPort(
            is_running_result=False,
            raise_error_on_start=LanguageModelServerStartFailed(),
        )
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        with self.assertLogs(
            "src.domain.language_model.language_model_server_starter", level="INFO"
        ) as captured_logs:
            with self.assertRaises(LanguageModelServerStartFailed):
                starter.ensure_running()

        self.assertEqual(len(captured_logs.records), 1)
        self.assertNotIn("started in", captured_logs.output[0])

    def test_ensure_running_marks_server_in_use_when_already_running(self):
        fake_port = FakeLanguageModelServerPort(is_running_result=True)
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        starter.ensure_running()

        self.assertEqual(fake_port.mark_in_use_call_count, 1)

    def test_ensure_running_marks_server_in_use_after_starting_server(self):
        fake_port = FakeLanguageModelServerPort(is_running_result=False)
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        starter.ensure_running()

        self.assertEqual(fake_port.mark_in_use_call_count, 1)

    def test_release_marks_server_idle(self):
        fake_port = FakeLanguageModelServerPort(is_running_result=True)
        starter = LanguageModelServerStarter(language_model_server_port=fake_port)

        starter.release()

        self.assertEqual(fake_port.mark_idle_call_count, 1)
