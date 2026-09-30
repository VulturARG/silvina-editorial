"""
E2E test for main.py SilvinaEditorialAssistant orchestrator.
Runs in-process with mocked external dependencies (Ollama, Laya, LanguageTool, COM).
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

from src.infrastructure.tests.test_doubles.fake_laya_agent import FakeLayaAgent

# Path adjustment from tests/e2e/ → project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Inject language_tool_python mock before any import that might trigger it
if "language_tool_python" not in sys.modules:
    _mock_ltp = MagicMock()
    _mock_lt_instance = MagicMock()
    _mock_lt_instance.check.return_value = []
    _mock_ltp.LanguageTool.return_value = _mock_lt_instance
    sys.modules["language_tool_python"] = _mock_ltp

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "capacidades_razonamiento_emergente_LLMs.docx"
)

FIXTURE_PATH = os.path.abspath(FIXTURE_PATH)


def _make_ollama_client_mock(
    response=(
        "S4: SI\nS5: SI\nS6: SI\n\n"
        "**Claridad** [Puntuación: 8/10]\nTexto claro y bien redactado.\n\n"
        "**Coherencia** [Puntuación: 8/10]\nIdeas conectadas de forma coherente.\n\n"
        "**Argumentación** [Puntuación: 8/10]\nArgumentos sólidos y bien fundamentados.\n\n"
        "**Conclusiones** [Puntuación: 8/10]\nConclusiones claras y consistentes."
    ),
):
    """Return a mock ollama.Client whose generate() satisfies both the
    classification (S4/S5/S6) and quality (per-dimension) response parsers."""
    mock_client = MagicMock()
    mock_client.generate.return_value = {"response": response}
    return mock_client


def _make_laya_agent_fake():
    """Return a Laya agent double mirroring the Ollama mock: S4/S5/S6 affirmative, scores 8."""

    def choice(answer):
        return {"choice": answer, "probabilities": {answer: 1.0}, "answer_confidence": 1.0}

    def score(value):
        return {"score": value, "probabilities": {}, "answer_confidence": 1.0}

    return FakeLayaAgent(
        answers={
            "s4_intent": choice("SI"),
            "s5_evidence": choice("SI"),
            "s6_theory": choice("SI"),
            "editorial_verdict": choice("SUSTENTADA"),
            "research_line": choice("1"),
            "score_clarity": score(8.0),
            "score_coherence": score(8.0),
            "score_argumentation": score(8.0),
            "score_conclusions": score(8.0),
        }
    )


class TestCLIE2E(unittest.TestCase):
    """
    In-process E2E test: constructs SilvinaEditorialAssistant, calls
    analyze_document() with a real .docx fixture, verifies the result dict.
    """

    @classmethod
    def setUpClass(cls):
        cls.fixture_exists = os.path.exists(FIXTURE_PATH)

    def test_fixture_available(self):
        self.assertTrue(self.fixture_exists, f"Fixture not found at: {FIXTURE_PATH}")

    @unittest.skipUnless(os.path.exists(FIXTURE_PATH), "Fixture .docx not available")
    def test_analyze_document_returns_dict(self):
        mock_client = _make_ollama_client_mock()
        with (
            patch("ollama.Client", return_value=mock_client),
            patch(
                "src.infrastructure.wirings.analyze_document_use_case_wiring.load",
                return_value=_make_laya_agent_fake(),
            ),
            patch(
                "src.infrastructure.adapters.document.win32com_word_count_adapter."
                "WIN32COM_AVAILABLE",
                False,
            ),
        ):
            from main import SilvinaEditorialAssistant

            silvina = SilvinaEditorialAssistant()
            result = silvina.analyze_document(FIXTURE_PATH)
        self.assertIsInstance(result, dict)

    @unittest.skipUnless(os.path.exists(FIXTURE_PATH), "Fixture .docx not available")
    def test_result_has_required_keys(self):
        mock_client = _make_ollama_client_mock()
        with (
            patch("ollama.Client", return_value=mock_client),
            patch(
                "src.infrastructure.wirings.analyze_document_use_case_wiring.load",
                return_value=_make_laya_agent_fake(),
            ),
            patch(
                "src.infrastructure.adapters.document.win32com_word_count_adapter."
                "WIN32COM_AVAILABLE",
                False,
            ),
        ):
            from main import SilvinaEditorialAssistant

            silvina = SilvinaEditorialAssistant()
            result = silvina.analyze_document(FIXTURE_PATH)
        for key in [
            "filename",
            "document_info",
            "classification",
            "quality_analysis",
            "structure_validation",
        ]:
            self.assertIn(key, result)

    @unittest.skipUnless(os.path.exists(FIXTURE_PATH), "Fixture .docx not available")
    def test_classification_key_has_category(self):
        mock_client = _make_ollama_client_mock()
        with (
            patch("ollama.Client", return_value=mock_client),
            patch(
                "src.infrastructure.wirings.analyze_document_use_case_wiring.load",
                return_value=_make_laya_agent_fake(),
            ),
            patch(
                "src.infrastructure.adapters.document.win32com_word_count_adapter."
                "WIN32COM_AVAILABLE",
                False,
            ),
        ):
            from main import SilvinaEditorialAssistant

            silvina = SilvinaEditorialAssistant()
            result = silvina.analyze_document(FIXTURE_PATH)
        self.assertIn("category", result["classification"])

    @unittest.skipUnless(os.path.exists(FIXTURE_PATH), "Fixture .docx not available")
    def test_document_info_has_word_count(self):
        mock_client = _make_ollama_client_mock()
        with (
            patch("ollama.Client", return_value=mock_client),
            patch(
                "src.infrastructure.wirings.analyze_document_use_case_wiring.load",
                return_value=_make_laya_agent_fake(),
            ),
            patch(
                "src.infrastructure.adapters.document.win32com_word_count_adapter."
                "WIN32COM_AVAILABLE",
                False,
            ),
        ):
            from main import SilvinaEditorialAssistant

            silvina = SilvinaEditorialAssistant()
            result = silvina.analyze_document(FIXTURE_PATH)
        self.assertGreater(result["document_info"]["word_count"], 0)


if __name__ == "__main__":
    unittest.main()
