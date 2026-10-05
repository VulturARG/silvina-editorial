from os import environ
from os.path import join
from tempfile import TemporaryDirectory


class IsolatedTestEnvironment:
    """Provides isolated filesystem paths and environment variables for test execution."""

    _temporary_directory: TemporaryDirectory[str] | None = None

    @classmethod
    def apply(cls) -> None:
        """Apply test environment isolation settings to os.environ."""
        if cls._temporary_directory is None:
            cls._temporary_directory = TemporaryDirectory(
                prefix="silvina-test-",
                ignore_cleanup_errors=True,
            )
        temporary_directory_path = cls._temporary_directory.name
        environ["TESTING"] = "True"
        environ["METRICS_DATABASE_PATH"] = join(temporary_directory_path, "metrics.db")
        environ["LOG_FILE_PATH"] = join(temporary_directory_path, "silvina.log")
        environ["USE_EXTERNAL_LLM"] = "false"
