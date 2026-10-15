from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.infrastructure.adapters.llm_generator.ollama_executable_locator import (
    OllamaExecutableLocator,
    read_windows_persistent_path,
)


class TestOllamaExecutableLocator(TestCase):
    def test_locate_returns_process_path_hit_first_without_consulting_registry_or_appdata(
        self,
    ):
        fake_which = MagicMock(return_value="C:\\bin\\ollama.exe")
        fake_persistent_reader = MagicMock()
        fake_file_checker = MagicMock()

        locator = OllamaExecutableLocator(
            which_function=fake_which,
            persistent_path_reader=fake_persistent_reader,
            local_app_data_directory_provider=lambda: "C:\\Users\\test\\AppData\\Local",
            file_existence_checker=fake_file_checker,
            operating_system_name="nt",
        )

        result = locator.locate()

        self.assertEqual(result, "C:\\bin\\ollama.exe")
        fake_which.assert_called_once_with("ollama")
        fake_persistent_reader.assert_not_called()
        fake_file_checker.assert_not_called()

    def test_locate_falls_back_to_registry_path_when_process_path_misses_on_windows(
        self,
    ):
        def _fake_which(command_name: str, path: str | None = None) -> str | None:
            if path == "E:\\Ollama":
                return "E:\\Ollama\\ollama.exe"
            return None

        fake_persistent_reader = MagicMock(return_value="E:\\Ollama")
        fake_file_checker = MagicMock()

        locator = OllamaExecutableLocator(
            which_function=_fake_which,
            persistent_path_reader=fake_persistent_reader,
            local_app_data_directory_provider=lambda: "C:\\Users\\test\\AppData\\Local",
            file_existence_checker=fake_file_checker,
            operating_system_name="nt",
        )

        result = locator.locate()

        self.assertEqual(result, "E:\\Ollama\\ollama.exe")
        fake_persistent_reader.assert_called_once()
        fake_file_checker.assert_not_called()

    def test_locate_falls_back_to_local_appdata_when_registry_path_misses_on_windows(
        self,
    ):
        fake_which = MagicMock(return_value=None)
        fake_persistent_reader = MagicMock(return_value="")
        expected_path = Path("C:\\Users\\test\\AppData\\Local\\Programs\\Ollama\\ollama.exe")

        def _fake_file_checker(candidate_path: Path) -> bool:
            return candidate_path == expected_path

        locator = OllamaExecutableLocator(
            which_function=fake_which,
            persistent_path_reader=fake_persistent_reader,
            local_app_data_directory_provider=lambda: "C:\\Users\\test\\AppData\\Local",
            file_existence_checker=_fake_file_checker,
            operating_system_name="nt",
        )

        result = locator.locate()

        self.assertEqual(result, str(expected_path))

    def test_locate_returns_none_when_nothing_found_on_windows(self):
        fake_which = MagicMock(return_value=None)
        fake_persistent_reader = MagicMock(return_value="")

        locator = OllamaExecutableLocator(
            which_function=fake_which,
            persistent_path_reader=fake_persistent_reader,
            local_app_data_directory_provider=lambda: "C:\\Users\\test\\AppData\\Local",
            file_existence_checker=lambda path: False,
            operating_system_name="nt",
        )

        result = locator.locate()

        self.assertIsNone(result)

    def test_locate_never_consults_registry_or_local_appdata_on_non_windows(self):
        fake_which = MagicMock(return_value=None)
        fake_persistent_reader = MagicMock()
        fake_file_checker = MagicMock()

        locator = OllamaExecutableLocator(
            which_function=fake_which,
            persistent_path_reader=fake_persistent_reader,
            local_app_data_directory_provider=lambda: "/home/user/.local/share",
            file_existence_checker=fake_file_checker,
            operating_system_name="posix",
        )

        result = locator.locate()

        self.assertIsNone(result)
        fake_which.assert_called_once_with("ollama")
        fake_persistent_reader.assert_not_called()
        fake_file_checker.assert_not_called()

    def test_read_windows_persistent_path_handles_missing_keys_and_os_errors(self):
        with patch(
            "src.infrastructure.adapters.llm_generator.ollama_executable_locator.OpenKey",
            side_effect=OSError("key not found"),
        ):
            persistent_path = read_windows_persistent_path()

        self.assertEqual(persistent_path, "")

    def test_read_windows_persistent_path_expands_environment_variables(self):
        mock_open_key = MagicMock()
        mock_query_value = MagicMock(
            side_effect=[
                ("%USERPROFILE%\\Ollama", 1),
                ("%SYSTEMROOT%\\Ollama", 1),
            ]
        )

        with (
            patch(
                "src.infrastructure.adapters.llm_generator.ollama_executable_locator.OpenKey",
                mock_open_key,
            ),
            patch(
                "src.infrastructure.adapters.llm_generator.ollama_executable_locator.QueryValueEx",
                mock_query_value,
            ),
            patch(
                "src.infrastructure.adapters.llm_generator.ollama_executable_locator.expandvars",
                side_effect=lambda value: value.replace("%USERPROFILE%", "C:\\Users\\test").replace(
                    "%SYSTEMROOT%", "C:\\Windows"
                ),
            ),
        ):
            persistent_path = read_windows_persistent_path()

        self.assertIn("C:\\Users\\test\\Ollama", persistent_path)
        self.assertIn("C:\\Windows\\Ollama", persistent_path)

    def test_locate_logs_source_when_found(self):
        fake_which = MagicMock(return_value="/usr/local/bin/ollama")
        locator = OllamaExecutableLocator(
            which_function=fake_which,
            operating_system_name="posix",
        )

        with self.assertLogs(
            "src.infrastructure.adapters.llm_generator.ollama_executable_locator",
            level="INFO",
        ) as captured_logs:
            locator.locate()

        self.assertEqual(len(captured_logs.records), 1)
        self.assertIn("/usr/local/bin/ollama", captured_logs.output[0])

    def test_locate_logs_warning_when_not_found(self):
        fake_which = MagicMock(return_value=None)
        locator = OllamaExecutableLocator(
            which_function=fake_which,
            operating_system_name="posix",
        )

        with self.assertLogs(
            "src.infrastructure.adapters.llm_generator.ollama_executable_locator",
            level="WARNING",
        ) as captured_logs:
            locator.locate()

        self.assertEqual(len(captured_logs.records), 1)
        self.assertIn("not found", captured_logs.output[0].lower())
