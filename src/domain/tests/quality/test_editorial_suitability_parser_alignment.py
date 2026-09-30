from unittest import TestCase

from src.domain.quality.editorial_suitability_parser import EditorialSuitabilityParser


class TestEditorialSuitabilityParserAlignment(TestCase):
    def setUp(self):
        self.parser = EditorialSuitabilityParser()

    def test_no_alineado_is_not_misdetected_as_alineado(self):
        raw = "VEREDICTO: NO ALINEADO\nJUSTIFICACION: No se identifica relacion con ninguna linea de investigacion vigente.\n"

        verdict, _lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "NO ALINEADO")
        self.assertEqual(
            justification,
            "No se identifica relacion con ninguna linea de investigacion vigente.",
        )

    def test_parcialmente_alineado_is_not_misdetected_as_alineado(self):
        raw = "VEREDICTO: PARCIALMENTE ALINEADO\nLINEAS: Linea 3 (tecnologia).\n"

        verdict, lines, _justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "PARCIALMENTE ALINEADO")
        self.assertEqual(lines, "Linea 3 (tecnologia).")

    def test_long_justification_truncated_at_word_boundary_with_ellipsis(self):
        raw = f"VEREDICTO: ALINEADO\nJUSTIFICACION: {'WORD ' * 30}END.\n"

        verdict, _lines, justification = self.parser.parse_alignment(raw)

        expected_prefix = "WORD " * 22 + "WORD"
        self.assertEqual(verdict, "ALINEADO")
        self.assertEqual(justification, expected_prefix + "…")
        self.assertLess(len(justification), 120)
        self.assertFalse(justification.endswith("WOR…"))

    def test_long_lines_truncated_to_eighty_characters_at_word_boundary(self):
        raw = f"VEREDICTO: ALINEADO\nLINEAS: {'WORD ' * 20}END.\n"

        _verdict, lines, _justification = self.parser.parse_alignment(raw)

        expected_prefix = "WORD " * 14 + "WORD"
        self.assertEqual(lines, expected_prefix + "…")
        self.assertLess(len(lines), 80)

    def test_resolve_research_line_title_extracts_id_and_title(self):
        research_lines = "1. Inteligencia Artificial y Sociedad\n2. Sistemas Embebidos"

        resolved_title = self.parser.resolve_research_line_title(research_lines, "1")

        self.assertEqual(resolved_title, "1. Inteligencia Artificial y Sociedad")

    def test_resolve_research_line_title_strips_em_dash_and_trailing_description(self):
        research_lines = "1. Inteligencia Artificial — Estudio del impacto social y tecnico"

        resolved_title = self.parser.resolve_research_line_title(research_lines, "1")

        self.assertEqual(resolved_title, "1. Inteligencia Artificial")

    def test_resolve_research_line_title_returns_line_id_when_not_found(self):
        research_lines = "1. Inteligencia Artificial\n2. Sistemas Embebidos"

        resolved_title = self.parser.resolve_research_line_title(research_lines, "99")

        self.assertEqual(resolved_title, "99")
