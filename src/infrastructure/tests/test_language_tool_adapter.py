import shutil
from importlib.util import find_spec
from typing import Any
from unittest import TestCase, skipIf
from unittest.mock import MagicMock, patch

from src.domain.exceptions.grammar_errors import GrammarCheckUnavailable
from src.infrastructure.adapters.grammar.language_tool_settings import (
    LanguageToolSettings,
)

_JAVA_AVAILABLE = shutil.which("java") is not None
_LANGUAGE_TOOL_AVAILABLE = find_spec("language_tool_python") is not None

if _LANGUAGE_TOOL_AVAILABLE:
    from src.infrastructure.adapters.grammar.language_tool_adapter import LanguageToolAdapter
else:
    LanguageToolAdapter: Any = None


@skipIf(
    not _JAVA_AVAILABLE or not _LANGUAGE_TOOL_AVAILABLE,
    "Java or language_tool_python not available",
)
class TestLanguageToolAdapter(TestCase):
    def _build_adapter(
        self,
        max_replacements: int = 3,
        max_paragraphs: int = 20,
        max_chars: int = 5000,
        max_errors: int = 10,
        language: str = "es",
    ) -> Any:
        language_tool_settings = LanguageToolSettings(
            max_replacements=max_replacements,
            max_paragraphs=max_paragraphs,
            max_chars=max_chars,
            max_errors=max_errors,
        )
        return LanguageToolAdapter(
            language_tool_settings=language_tool_settings,
            language=language,
        )

    def test_constructor_requires_all_parameters_raising_type_error_when_missing(self):
        kwargs: dict[str, Any] = {}
        with self.assertRaises(TypeError):
            LanguageToolAdapter(**kwargs)

    def test_constructor_defaults_language_to_spanish(self):
        language_tool_settings = LanguageToolSettings(
            max_replacements=3,
            max_paragraphs=20,
            max_chars=5000,
            max_errors=10,
        )
        adapter = LanguageToolAdapter(language_tool_settings=language_tool_settings)
        self.assertEqual(adapter._language, "es")

    def test_tool_is_none_after_construction_before_any_check_call(self):
        adapter = self._build_adapter()
        self.assertIsNone(adapter._tool)

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_misspelling_matches_are_filtered_from_results(self, mock_language_tool_python):
        mock_tool = MagicMock()
        mock_language_tool_python.LanguageTool.return_value = mock_tool

        grammar_match = MagicMock()
        grammar_match.rule_issue_type = "grammar"
        grammar_match.message = "Grammar error"
        grammar_match.context = "some context"
        grammar_match.offset = 0
        grammar_match.error_length = 4
        grammar_match.replacements = ["fix"]

        spelling_match = MagicMock()
        spelling_match.rule_issue_type = "misspelling"

        mock_tool.check.return_value = [grammar_match, spelling_match, grammar_match]

        adapter = self._build_adapter()
        result = adapter.check(paragraphs=["some text"])

        self.assertEqual(len(result), 2)

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_output_is_capped_at_ten_errors(self, mock_language_tool_python):
        mock_tool = MagicMock()
        mock_language_tool_python.LanguageTool.return_value = mock_tool

        def make_match(index: int) -> MagicMock:
            match = MagicMock()
            match.rule_issue_type = "grammar"
            match.message = f"error {index}"
            match.context = "ctx"
            match.offset = 0
            match.error_length = 3
            match.replacements = []
            return match

        mock_tool.check.return_value = [make_match(index=index) for index in range(12)]

        adapter = self._build_adapter()
        result = adapter.check(paragraphs=["text"])

        self.assertEqual(len(result), 10)

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_raises_grammar_check_unavailable_on_backend_failure(self, mock_language_tool_python):
        mock_language_tool_python.LanguageTool.side_effect = RuntimeError("Java crash")

        adapter = self._build_adapter()

        with self.assertRaises(GrammarCheckUnavailable):
            adapter.check(paragraphs=["text"])

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_custom_max_replacements_limits_suggestions_per_error(self, mock_language_tool_python):
        mock_tool = MagicMock()
        mock_language_tool_python.LanguageTool.return_value = mock_tool

        grammar_match = MagicMock()
        grammar_match.rule_issue_type = "grammar"
        grammar_match.message = "Grammar error"
        grammar_match.context = "some context"
        grammar_match.offset = 0
        grammar_match.error_length = 4
        grammar_match.replacements = ["a", "b", "c", "d", "e"]

        mock_tool.check.return_value = [grammar_match]

        adapter = self._build_adapter(max_replacements=2)
        result = adapter.check(paragraphs=["some text"])

        self.assertEqual(len(result[0].replacements), 2)

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_default_max_replacements_caps_suggestions_at_three(self, mock_language_tool_python):
        mock_tool = MagicMock()
        mock_language_tool_python.LanguageTool.return_value = mock_tool

        grammar_match = MagicMock()
        grammar_match.rule_issue_type = "grammar"
        grammar_match.message = "Grammar error"
        grammar_match.context = "some context"
        grammar_match.offset = 0
        grammar_match.error_length = 4
        grammar_match.replacements = ["a", "b", "c", "d", "e"]

        mock_tool.check.return_value = [grammar_match]

        adapter = self._build_adapter(max_replacements=3)
        result = adapter.check(paragraphs=["some text"])

        self.assertEqual(len(result[0].replacements), 3)

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_custom_max_paragraphs_and_max_chars_limit_sample_text(self, mock_language_tool_python):
        mock_tool = MagicMock()
        mock_language_tool_python.LanguageTool.return_value = mock_tool
        mock_tool.check.return_value = []

        adapter = self._build_adapter(max_paragraphs=2, max_chars=15)
        adapter.check(paragraphs=["Parrafo uno largo.", "Parrafo dos.", "Parrafo tres."])

        passed_text = mock_tool.check.call_args[0][0]
        self.assertEqual(passed_text, "Parrafo uno lar")

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_custom_max_errors_caps_returned_error_count(self, mock_language_tool_python):
        mock_tool = MagicMock()
        mock_language_tool_python.LanguageTool.return_value = mock_tool

        def make_match(index: int) -> MagicMock:
            match = MagicMock()
            match.rule_issue_type = "grammar"
            match.message = f"error {index}"
            match.context = "ctx"
            match.offset = 0
            match.error_length = 3
            match.replacements = []
            return match

        mock_tool.check.return_value = [make_match(index=index) for index in range(10)]

        adapter = self._build_adapter(max_errors=4)
        result = adapter.check(paragraphs=["text"])

        self.assertEqual(len(result), 4)
