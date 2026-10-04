from unittest import TestCase

from src.domain.quality.suitability_field_extractor import SuitabilityFieldExtractor


class TestSuitabilityFieldExtractor(TestCase):
    def setUp(self) -> None:
        self.extractor = SuitabilityFieldExtractor()

    def test_clean_value_strips_paired_asterisks_and_leading_markdown_characters(self) -> None:
        raw_text = "** : **texto con **negrita** interna**"

        result = self.extractor.clean_value(raw_text)

        self.assertEqual(result, "texto con negrita interna")

    def test_extract_verdict_text_finds_verdict_and_returns_uppercase(self) -> None:
        text = "VEREDICTO: sustentada\nCONTRIBUCION: texto"

        result = self.extractor.extract_verdict_text(text)

        self.assertEqual(result, "SUSTENTADA")

    def test_extract_verdict_text_handles_bold_label_with_colon_inside(self) -> None:
        text = "**VEREDICTO:** PARCIAL\nCONTRIBUCION: texto"

        result = self.extractor.extract_verdict_text(text)

        self.assertEqual(result, "PARCIAL")

    def test_extract_verdict_text_handles_bold_label_with_colon_outside(self) -> None:
        text = "**VEREDICTO**: NO SUSTENTADA\nCONTRIBUCION: texto"

        result = self.extractor.extract_verdict_text(text)

        self.assertEqual(result, "NO SUSTENTADA")

    def test_extract_verdict_text_returns_empty_string_when_label_missing(self) -> None:
        text = "TEXTO SIN ETIQUETA DE VEREDICTO"

        result = self.extractor.extract_verdict_text(text)

        self.assertEqual(result, "")

    def test_extract_contribution_phrase_handles_unaccented_label(self) -> None:
        text = "VEREDICTO: SUSTENTADA\nCONTRIBUCION: Aporte relevante al area."

        result = self.extractor.extract_contribution_phrase(text)

        self.assertEqual(result, "Aporte relevante al area.")

    def test_extract_contribution_phrase_handles_accented_label(self) -> None:
        text = "VEREDICTO: SUSTENTADA\nCONTRIBUCIÓN: Aporte relevante con acento."

        result = self.extractor.extract_contribution_phrase(text)

        self.assertEqual(result, "Aporte relevante con acento.")

    def test_extract_contribution_phrase_strips_internal_markdown_asterisks(self) -> None:
        text = "CONTRIBUCION: Propone la **sintesis** metodologica."

        result = self.extractor.extract_contribution_phrase(text)

        self.assertEqual(result, "Propone la sintesis metodologica.")

    def test_extract_contribution_phrase_returns_empty_string_when_missing(self) -> None:
        text = "VEREDICTO: SUSTENTADA\n"

        result = self.extractor.extract_contribution_phrase(text)

        self.assertEqual(result, "")

    def test_extract_justification_handles_unaccented_label(self) -> None:
        text = "JUSTIFICACION: Justificacion tecnica suficiente."

        result = self.extractor.extract_justification(text)

        self.assertEqual(result, "Justificacion tecnica suficiente.")

    def test_extract_justification_handles_accented_label(self) -> None:
        text = "JUSTIFICACIÓN: Justificación tecnica con acento."

        result = self.extractor.extract_justification(text)

        self.assertEqual(result, "Justificación tecnica con acento.")

    def test_extract_justification_returns_empty_string_when_missing(self) -> None:
        text = "VEREDICTO: ALINEADO\n"

        result = self.extractor.extract_justification(text)

        self.assertEqual(result, "")

    def test_extract_lines_same_line_captures_value_on_same_line(self) -> None:
        text = "LINEAS: Linea 4 (ciberespacio) y Linea 6.\nJUSTIFICACION: ok"

        result = self.extractor.extract_lines_same_line(text)

        self.assertEqual(result, "Linea 4 (ciberespacio) y Linea 6.")

    def test_extract_lines_same_line_handles_accented_label(self) -> None:
        text = "LÍNEAS: Linea 1 y Linea 2.\nJUSTIFICACION: ok"

        result = self.extractor.extract_lines_same_line(text)

        self.assertEqual(result, "Linea 1 y Linea 2.")

    def test_extract_lines_same_line_returns_empty_string_when_value_on_next_line(self) -> None:
        text = "LINEAS:\n- Linea 4: Ciberespacio\nJUSTIFICACION: ok"

        result = self.extractor.extract_lines_same_line(text)

        self.assertEqual(result, "")

    def test_repeated_and_interleaved_calls_produce_identical_results(self) -> None:
        sample_a = "VEREDICTO: SUSTENTADA\nCONTRIBUCION: Frase A"
        sample_b = "VEREDICTO: PARCIAL\nCONTRIBUCION: Frase B"

        phrase_a_first = self.extractor.extract_contribution_phrase(sample_a)
        phrase_b_first = self.extractor.extract_contribution_phrase(sample_b)
        phrase_a_second = self.extractor.extract_contribution_phrase(sample_a)
        phrase_b_second = self.extractor.extract_contribution_phrase(sample_b)

        self.assertEqual(phrase_a_first, phrase_a_second)
        self.assertEqual(phrase_b_first, phrase_b_second)
        self.assertEqual(phrase_a_first, "Frase A")
        self.assertEqual(phrase_b_first, "Frase B")
