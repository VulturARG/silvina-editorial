from os import environ
from pathlib import Path
from subprocess import run
from sys import executable
from unittest import TestCase

_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_PROBE_SCRIPT = """
import sys
import src.infrastructure.wirings.analyze_document_use_case_wiring
import src.infrastructure.wirings.external_llm_generator_loader
loaded_modules = sorted(
    name
    for name in sys.modules
    if name == "claude_agent_sdk"
    or name.startswith("claude_agent_sdk.")
    or name.endswith("claude_generator_adapter")
)
print(",".join(loaded_modules))
"""


class TestExternalLlmDependencyIsolation(TestCase):
    def test_importing_the_wiring_does_not_load_the_external_llm_sdk_or_adapter(self):
        completed_process = run(
            [executable, "-c", _PROBE_SCRIPT],
            cwd=_PROJECT_ROOT,
            env={**environ, "PYTHONPATH": str(_PROJECT_ROOT)},
            capture_output=True,
            text=True,
            timeout=60,
        )

        self.assertEqual(0, completed_process.returncode, completed_process.stderr)
        self.assertEqual("", completed_process.stdout.strip())
