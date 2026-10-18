from unittest import TestCase

from src.domain.quality.trailing_score_line_locator import TrailingScoreLineLocator

HEADER_WITHOUT_SCORE = "### 1. Claridad del argumento"
PROSE_LINE = "El texto organiza sus ideas con una progresión clara y sostenida."


class TestTrailingScoreLineLocator(TestCase):
    def setUp(self):
        self._locator = TrailingScoreLineLocator()

    def test_detects_bracketed_score_line_with_slash_ten(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\n[Puntuación: 8/10]"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_detects_plain_score_line_with_slash_ten(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPuntuación: 8/10"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_detects_bold_score_line(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\n**Puntuación: 8/10**"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_detects_score_line_wrapped_in_brackets_and_bold(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\n**[Puntuación: 8/10]**"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_detects_score_line_without_slash_ten(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPuntuación: 8"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_detects_decimal_score_line(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPuntuación: 7.5/10"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 7.5)

    def test_detects_score_line_with_final_period(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPuntuación: 8/10."

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_detects_score_line_without_accent(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPuntuacion: 8/10"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_detects_score_line_case_insensitively(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPUNTUACIÓN: 8/10"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_detects_score_line_with_surrounding_whitespace(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\n   Puntuación: 8/10   "

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_clamps_score_above_ten_to_ten(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPuntuación: 15/10"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 10.0)

    def test_ignores_trailing_blank_lines_after_score_line(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPuntuación: 8/10\n\n   \n"

        result = self._locator.locate(block)

        self.assertEqual(result.score, 8.0)

    def test_returns_block_without_score_line_and_without_trailing_blank_lines(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\n\nPuntuación: 8/10\n"

        result = self._locator.locate(block)

        self.assertEqual(
            result.block_without_score_line.strip(),
            f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}",
        )
        self.assertNotIn("Puntuación", result.block_without_score_line)

    def test_returns_none_when_header_already_carries_bracketed_score(self):
        block = f"**1. Claridad del argumento** [Puntuación: 8/10]\n{PROSE_LINE}\nPuntuación: 3/10"

        self.assertIsNone(self._locator.locate(block))

    def test_returns_none_when_header_already_carries_slash_ten_score(self):
        block = f"### 1. Claridad del argumento 8/10\n{PROSE_LINE}\nPuntuación: 3/10"

        self.assertIsNone(self._locator.locate(block))

    def test_returns_none_when_last_line_is_prose(self):
        block = f"{HEADER_WITHOUT_SCORE}\nPuntuación: 8/10\n{PROSE_LINE}"

        self.assertIsNone(self._locator.locate(block))

    def test_returns_none_when_score_line_is_not_the_last_non_empty_line(self):
        block = f"{HEADER_WITHOUT_SCORE}\nPuntuación: 8/10\n{PROSE_LINE}\n\n"

        self.assertIsNone(self._locator.locate(block))

    def test_returns_none_when_score_is_only_mentioned_inside_a_sentence(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE} Merece 5/10 en conjunto."

        self.assertIsNone(self._locator.locate(block))

    def test_returns_none_when_score_line_carries_extra_words(self):
        block = f"{HEADER_WITHOUT_SCORE}\n{PROSE_LINE}\nPuntuación: 8/10 sobre claridad"

        self.assertIsNone(self._locator.locate(block))

    def test_returns_none_when_block_has_no_non_empty_line_after_header(self):
        self.assertIsNone(self._locator.locate(f"{HEADER_WITHOUT_SCORE}\n\n"))
