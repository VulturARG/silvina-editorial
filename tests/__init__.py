"""
tests/__init__.py
Injects mock modules for win32com, pythoncom before any test imports.
This must run at package import time to intercept transitive imports.
"""

import sys
import io
from unittest.mock import MagicMock

from src.infrastructure.tests.isolated_test_environment import (
    IsolatedTestEnvironment,
)

IsolatedTestEnvironment.apply()

# Reconfigure stdout/stderr to UTF-8 on Windows to handle emoji in source print() calls.
# This prevents UnicodeEncodeError when source modules print emoji characters (⚠️, ✓, etc.)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Inject win32com mocks so modules that import win32com at the top level
# do not fail in environments without MS Office / Windows COM.
_win32com_client = MagicMock()

# win32com.client must be accessible as both sys.modules['win32com.client']
# AND as the 'client' attribute on sys.modules['win32com'] — they must be
# the same object so that win32com.client.DispatchEx lookups are consistent.
_win32com = MagicMock()
_win32com.client = _win32com_client

_pythoncom = MagicMock()

sys.modules.setdefault("win32com", _win32com)
sys.modules.setdefault("win32com.client", _win32com_client)
sys.modules.setdefault("pythoncom", _pythoncom)
