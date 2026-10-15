from collections.abc import Callable
from logging import getLogger
from os import environ, name, pathsep
from os.path import expandvars
from pathlib import Path
from shutil import which

try:
    from winreg import (
        HKEY_CURRENT_USER,
        HKEY_LOCAL_MACHINE,
        OpenKey,
        QueryValueEx,
    )

    CURRENT_USER_ROOT_KEY: int | None = HKEY_CURRENT_USER
    LOCAL_MACHINE_ROOT_KEY: int | None = HKEY_LOCAL_MACHINE
except ImportError:
    OpenKey = None
    QueryValueEx = None
    CURRENT_USER_ROOT_KEY = None
    LOCAL_MACHINE_ROOT_KEY = None

logger = getLogger(__name__)


def _read_registry_path_entry(root_key: int, subkey: str) -> str | None:
    if OpenKey is None or QueryValueEx is None:
        return None
    try:
        with OpenKey(root_key, subkey) as registry_key:
            value, _ = QueryValueEx(registry_key, "Path")
            if isinstance(value, str) and value.strip():
                return expandvars(value.strip())
    except OSError:
        return None
    return None


def read_windows_persistent_path() -> str:
    """Read and concatenate user and system PATH entries from the Windows registry."""
    path_entries: list[str] = []
    if CURRENT_USER_ROOT_KEY is not None:
        user_path = _read_registry_path_entry(CURRENT_USER_ROOT_KEY, r"Environment")
        if user_path:
            path_entries.append(user_path)
    if LOCAL_MACHINE_ROOT_KEY is not None:
        system_path = _read_registry_path_entry(
            LOCAL_MACHINE_ROOT_KEY,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        )
        if system_path:
            path_entries.append(system_path)
    return pathsep.join(path_entries)


class OllamaExecutableLocator:
    """Locates the Ollama executable in the system environment or installation folders."""

    def __init__(
        self,
        which_function: Callable[..., str | None] = which,
        persistent_path_reader: Callable[[], str] = read_windows_persistent_path,
        local_app_data_directory_provider: Callable[[], str | None] | None = None,
        file_existence_checker: Callable[[Path], bool] | None = None,
        operating_system_name: str = name,
    ) -> None:
        self._which_function = which_function
        self._persistent_path_reader = persistent_path_reader
        self._local_app_data_directory_provider = (
            local_app_data_directory_provider
            if local_app_data_directory_provider is not None
            else lambda: environ.get("LOCALAPPDATA")
        )
        self._file_existence_checker = (
            file_existence_checker
            if file_existence_checker is not None
            else lambda candidate_path: candidate_path.is_file()
        )
        self._operating_system_name = operating_system_name

    def locate(self, command_name: str = "ollama") -> str | None:
        """Find and return the path to the Ollama executable or None when not found."""
        process_path_hit = self._which_function(command_name)
        if process_path_hit:
            logger.info("Found Ollama executable in process PATH: %s", process_path_hit)
            return process_path_hit

        if self._operating_system_name == "nt":
            persistent_path = self._persistent_path_reader()
            if persistent_path:
                registry_hit = self._which_function(command_name, path=persistent_path)
                if registry_hit:
                    logger.info(
                        "Found Ollama executable in Windows persistent registry PATH: %s",
                        registry_hit,
                    )
                    return registry_hit

            local_app_data = self._local_app_data_directory_provider()
            if local_app_data:
                candidate_path = Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe"
                if self._file_existence_checker(candidate_path):
                    resolved_path = str(candidate_path)
                    logger.info(
                        "Found Ollama executable in default installation directory: %s",
                        resolved_path,
                    )
                    return resolved_path

        logger.warning(
            "Ollama executable not found in process PATH, persistent registry PATH, or default installation directory"
        )
        return None
