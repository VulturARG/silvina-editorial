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

    def test_bold_labels_with_colon_inside_bold_are_parsed_without_markdown(self):
        raw = (
            "**VEREDICTO:** PARCIALMENTE ALINEADO\n"
            "**LINEAS:** Línea 4 (ciberespacio) y Línea 6 (inteligencia).\n"
            "**JUSTIFICACION:** El artículo aborda mecanismos de razonamiento emergente.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "PARCIALMENTE ALINEADO")
        self.assertEqual(lines, "Línea 4 (ciberespacio) y Línea 6 (inteligencia).")
        self.assertEqual(
            justification,
            "El artículo aborda mecanismos de razonamiento emergente.",
        )
        self.assertFalse(lines.startswith("*"))
        self.assertFalse(lines.startswith(":"))
        self.assertFalse(lines.startswith(" "))
        self.assertNotIn("**", lines)
        self.assertFalse(justification.startswith("*"))
        self.assertFalse(justification.startswith(":"))
        self.assertFalse(justification.startswith(" "))
        self.assertNotIn("**", justification)

    def test_bold_labels_with_colon_outside_bold_are_parsed_without_markdown(self):
        raw = (
            "**VEREDICTO**: PARCIALMENTE ALINEADO\n"
            "**LINEAS**: Línea 4 (ciberespacio) y Línea 6 (inteligencia).\n"
            "**JUSTIFICACION**: El artículo aborda mecanismos de razonamiento emergente.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "PARCIALMENTE ALINEADO")
        self.assertEqual(lines, "Línea 4 (ciberespacio) y Línea 6 (inteligencia).")
        self.assertEqual(
            justification,
            "El artículo aborda mecanismos de razonamiento emergente.",
        )
        self.assertFalse(lines.startswith("*"))
        self.assertFalse(lines.startswith(":"))
        self.assertFalse(lines.startswith(" "))
        self.assertNotIn("**", lines)
        self.assertFalse(justification.startswith("*"))
        self.assertFalse(justification.startswith(":"))
        self.assertFalse(justification.startswith(" "))
        self.assertNotIn("**", justification)

    def test_paired_bold_in_middle_of_lines_and_justification_is_stripped(self):
        raw = (
            "VEREDICTO: PARCIALMENTE ALINEADO\n"
            "LINEAS: Línea 4 sobre **ciberespacio** e IA.\n"
            "JUSTIFICACION: Aborda la **síntesis** de tres modelos.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "PARCIALMENTE ALINEADO")
        self.assertEqual(lines, "Línea 4 sobre ciberespacio e IA.")
        self.assertEqual(justification, "Aborda la síntesis de tres modelos.")
        self.assertNotIn("**", lines)
        self.assertNotIn("**", justification)
