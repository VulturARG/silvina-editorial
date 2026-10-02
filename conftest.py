"""
conftest.py
Pytest configuration — applies to all tests.
"""

import sys
from io import TextIOWrapper
from logging import getLogger
from os import environ
from os.path import join
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from pytest import fixture

# Mark the test session so EnvConfig skips the version.txt file read and
# falls back to the SILVINA_VERSION env var instead.
environ["TESTING"] = "True"

# Isolate the metrics database and the log file to a temporary directory so that
# instantiating the wiring or configuring logging during tests never creates
# data/metrics.db or logs/silvina.log inside the repository.
_metrics_test_directory = TemporaryDirectory(prefix="silvina-metrics-")
environ.setdefault("METRICS_DATABASE_PATH", join(_metrics_test_directory.name, "metrics.db"))
environ.setdefault("LOG_FILE_PATH", join(_metrics_test_directory.name, "silvina.log"))

# Never let a developer's local .env enable the external LLM during tests: the wiring would
# call the real provider instead of the mocked Ollama client.
environ["USE_EXTERNAL_LLM"] = "false"

# Reconfigure stdout/stderr to UTF-8 so that emoji in source print() calls
# don't cause UnicodeEncodeError on Windows cp1252 consoles.
if isinstance(sys.stdout, TextIOWrapper):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if isinstance(sys.stderr, TextIOWrapper):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Inject win32com mocks at the start of the pytest session.
# This ensures modules that import win32com at the top level do not fail.
if "win32com" not in sys.modules:
    _win32com_client = MagicMock()
    _win32com = MagicMock()
    _win32com.client = _win32com_client
    sys.modules["win32com"] = _win32com
    sys.modules["win32com.client"] = _win32com_client
    sys.modules["pythoncom"] = MagicMock()


# Snapshot and restore the root logger handlers and level before and after each
# test to prevent log file locking and handler pollution across tests.
@fixture(autouse=True)
def isolate_root_logger():
    root_logger = getLogger()
    initial_handlers = list(root_logger.handlers)
    initial_level = root_logger.level
    try:
        yield
    finally:
        for handler in list(root_logger.handlers):
            if handler not in initial_handlers:
                root_logger.removeHandler(handler)
                handler.close()
        root_logger.setLevel(initial_level)
