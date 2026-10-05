"""Tests for ensuring package imports remain free of side effects."""

from os import environ
from pathlib import Path
from subprocess import run
from sys import executable
from tempfile import TemporaryDirectory
from unittest import TestCase


class TestPackageImportSideEffects(TestCase):
    """Verifies that importing packages does not trigger side-effect imports."""

    def test_importing_fastapi_package_does_not_import_dependencies_or_wirings(
        self,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[4]
        code = (
            "import sys\n"
            "import src.infrastructure.fastapi\n"
            "dependencies_present = 'src.infrastructure.fastapi.src.config.dependencies' in sys.modules\n"
            "wiring_present = 'src.infrastructure.wirings.analyze_document_use_case_wiring' in sys.modules\n"
            "print(dependencies_present)\n"
            "print(wiring_present)\n"
        )
        with TemporaryDirectory(
            prefix="silvina-test-fastapi-import-",
        ) as temporary_directory:
            temporary_directory_path = Path(temporary_directory)
            environment = dict(environ)
            environment["METRICS_DATABASE_PATH"] = str(temporary_directory_path / "metrics.db")
            environment["LOG_FILE_PATH"] = str(temporary_directory_path / "silvina.log")
            completed_process = run(
                [executable, "-c", code],
                cwd=repository_root,
                capture_output=True,
                text=True,
                timeout=60,
                env=environment,
            )

        self.assertEqual(completed_process.returncode, 0, completed_process.stderr)
        output_lines = completed_process.stdout.strip().splitlines()
        self.assertEqual(len(output_lines), 2)
        dependencies_imported = output_lines[0] == "True"
        wiring_imported = output_lines[1] == "True"
        self.assertFalse(dependencies_imported)
        self.assertFalse(wiring_imported)

    def test_importing_fastapi_routes_package_does_not_create_metrics_database(
        self,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[4]
        code = "import src.infrastructure.fastapi.src.routes\n"
        with TemporaryDirectory(
            prefix="silvina-test-routes-import-",
        ) as temporary_directory:
            temporary_directory_path = Path(temporary_directory)
            database_path = temporary_directory_path / "metrics.db"
            log_path = temporary_directory_path / "silvina.log"
            environment = dict(environ)
            environment["METRICS_DATABASE_PATH"] = str(database_path)
            environment["LOG_FILE_PATH"] = str(log_path)
            environment["USE_EXTERNAL_LLM"] = "false"
            completed_process = run(
                [executable, "-c", code],
                cwd=repository_root,
                capture_output=True,
                text=True,
                timeout=120,
                env=environment,
            )

            self.assertEqual(completed_process.returncode, 0, completed_process.stderr)
            self.assertFalse(database_path.exists())

    def test_importing_fastapi_app_module_does_not_create_metrics_database(
        self,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[4]
        code = "import src.infrastructure.fastapi.fastapi_app\n"
        with TemporaryDirectory(
            prefix="silvina-test-fastapi-app-import-",
        ) as temporary_directory:
            temporary_directory_path = Path(temporary_directory)
            database_path = temporary_directory_path / "metrics.db"
            log_path = temporary_directory_path / "silvina.log"
            environment = dict(environ)
            environment["METRICS_DATABASE_PATH"] = str(database_path)
            environment["LOG_FILE_PATH"] = str(log_path)
            environment["USE_EXTERNAL_LLM"] = "false"
            completed_process = run(
                [executable, "-c", code],
                cwd=repository_root,
                capture_output=True,
                text=True,
                timeout=120,
                env=environment,
            )

            self.assertEqual(completed_process.returncode, 0, completed_process.stderr)
            self.assertFalse(database_path.exists())
