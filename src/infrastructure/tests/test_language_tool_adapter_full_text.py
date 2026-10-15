import shutil
from importlib.util import find_spec
from typing import Any
from unittest import TestCase, skipIf
from unittest.mock import MagicMock, patch

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
class TestLanguageToolAdapterFullText(TestCase):
    def _build_adapter(self) -> Any:
        language_tool_settings = LanguageToolSettings(max_replacements=3)
        return LanguageToolAdapter(language_tool_settings=language_tool_settings)

    def _make_match(self, index: int, rule_issue_type: str = "grammar") -> MagicMock:
        match = MagicMock()
        match.rule_issue_type = rule_issue_type
        match.message = f"error {index}"
        match.context = "ctx"
        match.offset = 0
        match.error_length = 3
        match.replacements = []
        return match

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_sends_every_paragraph_joined_by_newline_to_the_tool_without_cutting(
        self, mock_language_tool_python
    ):
        mock_tool = MagicMock()
        mock_language_tool_python.LanguageTool.return_value = mock_tool
        mock_tool.check.return_value = []
        paragraphs = [f"Paragraph {index}." for index in range(25)]
        paragraphs.append("a" * 200_000)

        self._build_adapter().check(paragraphs=paragraphs)

        passed_text = mock_tool.check.call_args[0][0]
        self.assertEqual(passed_text, "\n".join(paragraphs))

    @patch("src.infrastructure.adapters.grammar.language_tool_adapter.language_tool_python")
    def test_returns_every_non_misspelling_match_beyond_ten_errors(self, mock_language_tool_python):
        mock_tool = MagicMock()
        mock_language_tool_python.LanguageTool.return_value = mock_tool
        grammar_matches = [self._make_match(index=index) for index in range(12)]
        mock_tool.check.return_value = [
            *grammar_matches[:5],
            self._make_match(index=99, rule_issue_type="misspelling"),
            *grammar_matches[5:],
        ]

        result = self._build_adapter().check(paragraphs=["text"])

        self.assertEqual(len(result), 12)
        self.assertEqual([error.number for error in result], list(range(1, 13)))
