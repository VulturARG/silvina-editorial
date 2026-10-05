"""
conftest.py
Pytest configuration — applies to all tests.
"""

import sys
from importlib.util import find_spec
from io import TextIOWrapper
from logging import getLogger
from unittest.mock import MagicMock

from pytest import fixture

from src.infrastructure.tests.isolated_test_environment import (
    IsolatedTestEnvironment,
)

# Isolate the metrics database and log file to a temporary directory so that
# running tests never creates data/metrics.db or logs/silvina.log inside the repository;
# mark the session with TESTING, and ensure a local .env never enables the external LLM.
IsolatedTestEnvironment.apply()

# The Claude Agent SDK is an optional debug-only dependency (requirements-debug.txt): without it,
# skip the tests that import it at module level instead of aborting the whole collection.
collect_ignore = []
if find_spec("claude_agent_sdk") is None:
    collect_ignore.append(
        "src/infrastructure/tests/adapters/llm_generator/test_claude_generator_adapter.py"
    )

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
