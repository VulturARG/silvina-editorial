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

    def test_long_lines_truncated_to_two_hundred_characters_at_word_boundary(self):
        raw = f"VEREDICTO: ALINEADO\nLINEAS: {'WORD ' * 45}END.\n"

        _verdict, lines, _justification = self.parser.parse_alignment(raw)

        expected_prefix = "WORD " * 38 + "WORD"
        self.assertEqual(lines, expected_prefix + "…")
        self.assertLess(len(lines), 200)

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

    def test_multiline_list_under_lineas_label_joined_with_semicolon(self):
        raw = (
            "VEREDICTO: PARCIALMENTE ALINEADO\n\n"
            "LINEAS: \n"
            "- Línea 4: Dinámica de los conflictos en el ciberespacio (IA y convergencia ciber-física)\n"
            "- Línea 6: Inteligencia en los diversos ámbitos de conflicto (IA y ciclo de inteligencia)\n"
            "- Línea 7: Ciencia, tecnología y producción en la defensa (IA y autonomía tecnológica)\n\n"
            "JUSTIFICACION: El artículo aborda mecanismos fundamentales de razonamiento emergente.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "PARCIALMENTE ALINEADO")
        self.assertFalse(lines.startswith("-"))
        self.assertTrue(lines.startswith("Línea 4: Dinámica de los conflictos en el ciberespacio"))
        self.assertLess(len(lines), 200)
        self.assertEqual(
            justification,
            "El artículo aborda mecanismos fundamentales de razonamiento emergente.",
        )

    def test_multiline_list_under_bold_lineas_label_joined_with_semicolon(self):
        raw = (
            "**VEREDICTO:** PARCIALMENTE ALINEADO\n\n"
            "**LINEAS:**\n"
            "- Línea 4: Ciberespacio e inteligencia artificial\n"
            "- Línea 6: Ciclo de inteligencia y toma de decisiones\n"
            "**JUSTIFICACION:** Conexión temática identificada.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "PARCIALMENTE ALINEADO")
        self.assertEqual(
            lines,
            "Línea 4: Ciberespacio e inteligencia artificial; Línea 6: Ciclo de inteligencia y toma de decisiones",
        )
        self.assertEqual(justification, "Conexión temática identificada.")

    def test_numbered_one_line_form_does_not_cut_at_first_number_period(self):
        raw = (
            "VEREDICTO: PARCIALMENTE ALINEADO\n\n"
            "LINEAS: 3. Recursos humanos para la defensa (factores humanos en IA); "
            "4. Dinámica de los conflictos en el ciberespacio (IA); "
            "7. Ciencia, tecnología y producción en la defensa (IA, sistemas autónomos).\n\n"
            "JUSTIFICACION: El artículo es un estudio técnico de ciencia cognitiva computacional.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "PARCIALMENTE ALINEADO")
        self.assertNotEqual(lines, "3.")
        self.assertTrue(lines.startswith("3. Recursos humanos para la defensa"))
        self.assertIn("4. Dinámica", lines)
        self.assertLess(len(lines), 200)
        self.assertEqual(
            justification,
            "El artículo es un estudio técnico de ciencia cognitiva computacional.",
        )

    def test_extract_first_sentence_does_not_stop_at_decimal_period(self):
        raw = (
            "VEREDICTO: ALINEADO\n"
            "LINEAS: Línea 1.5 de investigación tecnológica prioritaria. Segunda oración no relevante.\n"
            "JUSTIFICACION: Justificación adecuada.\n"
        )

        _verdict, lines, _justification = self.parser.parse_alignment(raw)

        self.assertEqual(
            lines,
            "Línea 1.5 de investigación tecnológica prioritaria.",
        )

    def test_plain_one_line_form_still_works(self):
        raw = (
            "VEREDICTO: ALINEADO\n"
            "LINEAS: Línea 4 (ciberespacio) y Línea 6 (inteligencia).\n"
            "JUSTIFICACION: Justificación breve y directa.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "ALINEADO")
        self.assertEqual(lines, "Línea 4 (ciberespacio) y Línea 6 (inteligencia).")
        self.assertEqual(justification, "Justificación breve y directa.")

    def test_multiline_list_under_lineas_label_with_blank_lines_before_list_is_captured(
        self,
    ):
        raw = (
            "VEREDICTO: PARCIALMENTE ALINEADO\n\n"
            "LINEAS:\n\n"
            "- Línea 4: Ciberespacio e inteligencia artificial\n"
            "- Línea 6: Ciclo de inteligencia y toma de decisiones\n\n"
            "JUSTIFICACION: Conexión temática identificada.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "PARCIALMENTE ALINEADO")
        self.assertEqual(
            lines,
            "Línea 4: Ciberespacio e inteligencia artificial; Línea 6: Ciclo de inteligencia y toma de decisiones",
        )
        self.assertEqual(justification, "Conexión temática identificada.")

    def test_multiline_numbered_list_with_multiple_blank_lines_before_list_is_captured(
        self,
    ):
        raw = (
            "VEREDICTO: ALINEADO\n\n"
            "**LINEAS:**\n\n\n"
            "1. Primera línea de investigación aplicada\n"
            "2. Segunda línea de investigación aplicada\n\n"
            "JUSTIFICACION: Justificación clara.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "ALINEADO")
        self.assertEqual(
            lines,
            "Primera línea de investigación aplicada; Segunda línea de investigación aplicada",
        )
        self.assertEqual(justification, "Justificación clara.")

    def test_sentence_ending_with_number_period_is_cut_at_period(self):
        raw = (
            "VEREDICTO: ALINEADO\n"
            "LINEAS: Se identifica alineación con la prioridad en la línea 4. Otra oración que debe descartarse.\n"
            "JUSTIFICACION: Justificación breve.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "ALINEADO")
        self.assertEqual(
            lines,
            "Se identifica alineación con la prioridad en la línea 4.",
        )
        self.assertEqual(justification, "Justificación breve.")

    def test_list_number_after_colon_stays_whole(self):
        raw = (
            "VEREDICTO: ALINEADO\n"
            "LINEAS: prioridades: 3. Recursos humanos para la defensa. Otra oración no relevante.\n"
            "JUSTIFICACION: Justificación breve.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "ALINEADO")
        self.assertEqual(
            lines,
            "prioridades: 3. Recursos humanos para la defensa.",
        )
        self.assertEqual(justification, "Justificación breve.")

    def test_list_number_after_hyphen_stays_whole(self):
        raw = (
            "VEREDICTO: ALINEADO\n"
            "LINEAS: - 3. Item relevante de investigación aplicada. Otra oración no relevante.\n"
            "JUSTIFICACION: Justificación breve.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "ALINEADO")
        self.assertEqual(
            lines,
            "- 3. Item relevante de investigación aplicada.",
        )
        self.assertEqual(justification, "Justificación breve.")

    def test_list_number_at_start_of_second_line_stays_whole(self):
        multiline_text = (
            "Línea introductoria\n"
            "3. Recursos humanos para la defensa. Segunda oración no relevante."
        )

        first_sentence = self.parser._extract_first_sentence(multiline_text)

        self.assertEqual(
            first_sentence,
            "Línea introductoria\n3. Recursos humanos para la defensa.",
        )

    def test_sentence_ending_with_hyphenated_numbers_is_cut_at_period(self):
        raw = (
            "VEREDICTO: ALINEADO\n"
            "LINEAS: líneas 3-5. Otra oración no relevante.\n"
            "JUSTIFICACION: Justificación breve.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "ALINEADO")
        self.assertEqual(lines, "líneas 3-5.")
        self.assertEqual(justification, "Justificación breve.")

    def test_sentence_ending_with_ratio_numbers_is_cut_at_period(self):
        raw = (
            "VEREDICTO: ALINEADO\n"
            "LINEAS: relación 3:4. Otra cosa no relevante.\n"
            "JUSTIFICACION: Justificación breve.\n"
        )

        verdict, lines, justification = self.parser.parse_alignment(raw)

        self.assertEqual(verdict, "ALINEADO")
        self.assertEqual(lines, "relación 3:4.")
        self.assertEqual(justification, "Justificación breve.")
