from os import environ
from pathlib import Path
from unittest import TestCase


class TestFastApiEnvironmentIsolation(TestCase):
    """Verifies that the FastAPI test package initializes isolated environment variables."""

    def test_environment_variables_are_isolated(self) -> None:
        repository_root_directory = Path(__file__).resolve().parents[4]
        repository_data_directory = (repository_root_directory / "data").resolve()
        repository_logs_directory = (repository_root_directory / "logs").resolve()

        self.assertIn("METRICS_DATABASE_PATH", environ)
        self.assertIn("LOG_FILE_PATH", environ)

        metrics_database_path = Path(environ["METRICS_DATABASE_PATH"]).resolve()
        log_file_path = Path(environ["LOG_FILE_PATH"]).resolve()

        self.assertFalse(metrics_database_path.is_relative_to(repository_data_directory))
        self.assertFalse(log_file_path.is_relative_to(repository_logs_directory))
        self.assertEqual(environ.get("USE_EXTERNAL_LLM"), "false")
