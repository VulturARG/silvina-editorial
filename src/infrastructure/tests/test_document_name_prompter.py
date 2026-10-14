from unittest import TestCase

from src.infrastructure.cli.document_name_prompter import DocumentNamePrompter


class TestDocumentNamePrompter(TestCase):
    PROMPT_TEXT = "Ingrese el nombre del documento (.docx): "

    @staticmethod
    def _ask_with_answer(answer: str) -> tuple[str, list[str]]:
        prompts_asked: list[str] = []

        def fake_input(prompt: str) -> str:
            prompts_asked.append(prompt)
            return answer

        document_name = DocumentNamePrompter(input_function=fake_input).ask()
        return document_name, prompts_asked

    def test_asks_with_spanish_prompt_text(self):
        _, prompts_asked = self._ask_with_answer("report.docx")

        self.assertEqual(prompts_asked, [self.PROMPT_TEXT])

    def test_returns_answer_unchanged_when_it_has_no_whitespace_or_quotes(self):
        document_name, _ = self._ask_with_answer("report.docx")

        self.assertEqual(document_name, "report.docx")

    def test_strips_surrounding_whitespace(self):
        document_name, _ = self._ask_with_answer("  report.docx \n")

        self.assertEqual(document_name, "report.docx")

    def test_strips_surrounding_double_quotes(self):
        document_name, _ = self._ask_with_answer('"report.docx"')

        self.assertEqual(document_name, "report.docx")

    def test_strips_whitespace_around_quoted_name(self):
        document_name, _ = self._ask_with_answer('  "C:\\Docs\\report.docx"  ')

        self.assertEqual(document_name, "C:\\Docs\\report.docx")

    def test_strips_whitespace_inside_quotes(self):
        document_name, _ = self._ask_with_answer('" report.docx "')

        self.assertEqual(document_name, "report.docx")
