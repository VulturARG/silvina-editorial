from os import environ
from os.path import exists
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from src.infrastructure.tests.isolated_test_environment import (
    IsolatedTestEnvironment,
)


class TestIsolatedTestEnvironment(TestCase):
    """Tests for IsolatedTestEnvironment."""

    @patch.dict(environ)
    def test_apply_replaces_database_and_log_paths_with_temporary_directory(
        self,
    ) -> None:
        repository_root_directory = Path(__file__).resolve().parents[3]
        repository_metrics_database_path = str(repository_root_directory / "data" / "metrics.db")
        repository_log_file_path = str(repository_root_directory / "logs" / "silvina.log")
        environ["METRICS_DATABASE_PATH"] = repository_metrics_database_path
        environ["LOG_FILE_PATH"] = repository_log_file_path

        IsolatedTestEnvironment.apply()

        configured_metrics_database_path = Path(environ["METRICS_DATABASE_PATH"]).resolve()
        configured_log_file_path = Path(environ["LOG_FILE_PATH"]).resolve()
        configured_temporary_directory = configured_metrics_database_path.parent

        self.assertEqual(configured_metrics_database_path.name, "metrics.db")
        self.assertEqual(configured_log_file_path.name, "silvina.log")
        self.assertEqual(
            configured_log_file_path.parent,
            configured_temporary_directory,
        )
        self.assertFalse(configured_temporary_directory.is_relative_to(repository_root_directory))

    @patch.dict(environ)
    def test_apply_forces_use_external_llm_to_false(self) -> None:
        environ["USE_EXTERNAL_LLM"] = "true"

        IsolatedTestEnvironment.apply()

        self.assertEqual(environ["USE_EXTERNAL_LLM"], "false")

    @patch.dict(environ)
    def test_apply_sets_testing_flag(self) -> None:
        environ.pop("TESTING", None)

        IsolatedTestEnvironment.apply()

        self.assertEqual(environ["TESTING"], "True")

    @patch.dict(environ)
    def test_apply_is_idempotent_reusing_same_directory(self) -> None:
        IsolatedTestEnvironment.apply()
        first_metrics_database_path = environ["METRICS_DATABASE_PATH"]
        first_log_file_path = environ["LOG_FILE_PATH"]

        IsolatedTestEnvironment.apply()
        second_metrics_database_path = environ["METRICS_DATABASE_PATH"]
        second_log_file_path = environ["LOG_FILE_PATH"]

        self.assertEqual(first_metrics_database_path, second_metrics_database_path)
        self.assertEqual(first_log_file_path, second_log_file_path)

    @patch.dict(environ)
    def test_apply_does_not_create_database_file(self) -> None:
        with patch.object(IsolatedTestEnvironment, "_temporary_directory", None):
            IsolatedTestEnvironment.apply()

            metrics_database_path = environ["METRICS_DATABASE_PATH"]

            self.assertFalse(exists(metrics_database_path))
            self.assertFalse(exists(environ["LOG_FILE_PATH"]))
