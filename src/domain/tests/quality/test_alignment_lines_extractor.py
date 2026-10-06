from unittest import TestCase

from src.domain.quality.alignment_lines_extractor import AlignmentLinesExtractor
from src.domain.quality.suitability_field_extractor import SuitabilityFieldExtractor


class TestAlignmentLinesExtractor(TestCase):
    def setUp(self) -> None:
        self.field_extractor = SuitabilityFieldExtractor()
        self.extractor = AlignmentLinesExtractor(field_extractor=self.field_extractor)

    def test_extract_returns_same_line_value_when_present(self) -> None:
        text = "LINEAS: Linea 3 (tecnologia).\nJUSTIFICACION: ok"

        result = self.extractor.extract(text)

        self.assertEqual(result, "Linea 3 (tecnologia).")

    def test_extract_handles_bold_label_with_colon_inside_bold_on_same_line(self) -> None:
        text = "**LINEAS:** Línea 4 (ciberespacio) y Línea 6.\nJUSTIFICACION: ok"

        result = self.extractor.extract(text)

        self.assertEqual(result, "Línea 4 (ciberespacio) y Línea 6.")

    def test_extract_handles_bold_label_with_colon_outside_bold_on_same_line(self) -> None:
        text = "**LINEAS**: Línea 4 (ciberespacio) y Línea 6.\nJUSTIFICACION: ok"

        result = self.extractor.extract(text)

        self.assertEqual(result, "Línea 4 (ciberespacio) y Línea 6.")

    def test_extract_handles_accented_label_on_same_line(self) -> None:
        text = "LÍNEAS: Línea 1 y Línea 2.\nJUSTIFICACION: ok"

        result = self.extractor.extract(text)

        self.assertEqual(result, "Línea 1 y Línea 2.")

    def test_extract_returns_empty_when_text_after_newline_is_not_a_list(self) -> None:
        text = "LÍNEAS:\nTexto libre sin lista en la primera linea\nJUSTIFICACIÓN: ok"

        result = self.extractor.extract(text)

        self.assertEqual(result, "")

    def test_extract_joins_multiline_bullet_list_with_semicolon(self) -> None:
        text = "LINEAS: \n- Línea 4: Ciberespacio\n- Línea 6: Inteligencia\nJUSTIFICACION: ok"

        result = self.extractor.extract(text)

        self.assertEqual(result, "Línea 4: Ciberespacio; Línea 6: Inteligencia")

    def test_extract_joins_multiline_numbered_list_with_semicolon(self) -> None:
        text = (
            "**LINEAS:**\n"
            "1. Primera línea de investigación aplicada\n"
            "2. Segunda línea de investigación aplicada\n"
            "JUSTIFICACION: ok"
        )

        result = self.extractor.extract(text)

        self.assertEqual(
            result,
            "Primera línea de investigación aplicada; Segunda línea de investigación aplicada",
        )

    def test_extract_skips_blank_lines_before_list_items(self) -> None:
        text = "LINEAS:\n\n\n- Línea 4: Ciberespacio\n- Línea 6: Inteligencia\nJUSTIFICACION: ok"

        result = self.extractor.extract(text)

        self.assertEqual(result, "Línea 4: Ciberespacio; Línea 6: Inteligencia")

    def test_extract_stops_list_at_next_uppercase_label(self) -> None:
        text = (
            "LINEAS:\n"
            "- Línea 4: Ciberespacio\n"
            "JUSTIFICACION: Detalle\n"
            "- Línea 6: Ignorada tras siguiente etiqueta"
        )

        result = self.extractor.extract(text)

        self.assertEqual(result, "Línea 4: Ciberespacio")

    def test_extract_stops_list_at_empty_line_after_list_starts(self) -> None:
        text = (
            "VEREDICTO: ALINEADO\n"
            "LÍNEAS:\n"
            "- Línea 4: Salud\n"
            "- Línea 6: Educación\n\n"
            "- Línea 7: Otra\n"
            "JUSTIFICACIÓN: ok"
        )

        result = self.extractor.extract(text)

        self.assertEqual(result, "Línea 4: Salud; Línea 6: Educación")

    def test_extract_strips_internal_markdown_asterisks_from_list_items(self) -> None:
        text = (
            "LINEAS:\n"
            "- Línea 4 sobre **ciberespacio** e IA\n"
            "- **Línea 6**: Inteligencia\n"
            "JUSTIFICACION: ok"
        )

        result = self.extractor.extract(text)

        self.assertEqual(
            result,
            "Línea 4 sobre ciberespacio e IA; Línea 6: Inteligencia",
        )

    def test_extract_returns_empty_string_when_label_absent(self) -> None:
        text = "VEREDICTO: ALINEADO\nJUSTIFICACION: Sin seccion de lineas."

        result = self.extractor.extract(text)

        self.assertEqual(result, "")

    def test_extract_blank_line_after_empty_item_does_not_stop_list_before_content(self) -> None:
        text = "LÍNEAS:\n- **\n\n- two"

        result = self.extractor.extract(text)

        self.assertEqual(result, "two")

    def test_extract_blank_line_with_empty_item_between_blanks_collects_first_non_empty_item(
        self,
    ) -> None:
        text = "LÍNEAS:\n\n- **\n\n- two\n\n- three"

        result = self.extractor.extract(text)

        self.assertEqual(result, "two")

    def test_extract_multiple_empty_items_before_blank_line_does_not_stop_list(self) -> None:
        text = "LÍNEAS:\n- **\n- **\n\n- x"

        result = self.extractor.extract(text)

        self.assertEqual(result, "x")

    def test_repeated_and_interleaved_calls_produce_identical_results(self) -> None:
        sample_a = "LINEAS: Linea A.\nJUSTIFICACION: ok"
        sample_b = "LINEAS:\n- Item 1\n- Item 2\nJUSTIFICACION: ok"

        result_a_first = self.extractor.extract(sample_a)
        result_b_first = self.extractor.extract(sample_b)
        result_a_second = self.extractor.extract(sample_a)
        result_b_second = self.extractor.extract(sample_b)

        self.assertEqual(result_a_first, result_a_second)
        self.assertEqual(result_b_first, result_b_second)
        self.assertEqual(result_a_first, "Linea A.")
        self.assertEqual(result_b_first, "Item 1; Item 2")
