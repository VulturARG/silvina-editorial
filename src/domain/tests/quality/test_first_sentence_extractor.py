from unittest import TestCase

from src.domain.quality.first_sentence_extractor import FirstSentenceExtractor


class TestFirstSentenceExtractor(TestCase):
    def setUp(self) -> None:
        self.extractor = FirstSentenceExtractor()

    def test_extract_first_sentence_stops_at_period(self) -> None:
        text = "Primera oracion completa. Segunda oracion no relevante."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "Primera oracion completa.")

    def test_extract_first_sentence_stops_at_exclamation_mark(self) -> None:
        text = "¡Atencion importante! Segunda oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "¡Atencion importante!")

    def test_extract_first_sentence_stops_at_question_mark(self) -> None:
        text = "¿Que es esto? Segunda oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "¿Que es esto?")

    def test_extract_first_sentence_does_not_stop_at_decimal_period(self) -> None:
        text = "Linea 1.5 de investigacion tecnologica prioritaria. Segunda oracion no relevante."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "Linea 1.5 de investigacion tecnologica prioritaria.")

    def test_extract_first_sentence_does_not_stop_at_multiple_decimals(self) -> None:
        text = "Mejora de 1.5% a 2.5% en rendimiento. Otra frase."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "Mejora de 1.5% a 2.5% en rendimiento.")

    def test_extract_first_sentence_preserves_list_number_at_start_of_text(self) -> None:
        text = "3. Recursos humanos para la defensa. Segunda oracion no relevante."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "3. Recursos humanos para la defensa.")

    def test_extract_first_sentence_preserves_two_digit_list_number_at_start(self) -> None:
        text = "12. Salud publica y epidemiologia. Segunda oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "12. Salud publica y epidemiologia.")

    def test_extract_first_sentence_preserves_list_number_after_newline(self) -> None:
        text = "Introduccion\n4. Ciberespacio y defensa. Segunda oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "Introduccion\n4. Ciberespacio y defensa.")

    def test_extract_first_sentence_preserves_list_number_after_semicolon(self) -> None:
        text = "item 1; 2. Segundo item relevante. Fin de lista."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "item 1; 2. Segundo item relevante.")

    def test_extract_first_sentence_preserves_list_number_after_comma(self) -> None:
        text = "item 1, 2. Segundo item relevante. Fin de lista."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "item 1, 2. Segundo item relevante.")

    def test_extract_first_sentence_preserves_list_number_in_parenthesis(self) -> None:
        text = "(1. Primer elemento relevante). Otra oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "(1. Primer elemento relevante).")

    def test_extract_first_sentence_preserves_list_number_in_brackets(self) -> None:
        text = "[2. Segundo elemento relevante]. Otra oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "[2. Segundo elemento relevante].")

    def test_extract_first_sentence_preserves_list_number_after_colon(self) -> None:
        text = "prioridades: 3. Recursos humanos para la defensa. Otra oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "prioridades: 3. Recursos humanos para la defensa.")

    def test_extract_first_sentence_preserves_list_number_after_hyphen(self) -> None:
        text = "- 3. Item relevante de investigacion aplicada. Otra oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "- 3. Item relevante de investigacion aplicada.")

    def test_extract_first_sentence_cuts_sentence_ending_with_hyphenated_numbers(self) -> None:
        text = "lineas 3-5. Otra oracion no relevante."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "lineas 3-5.")

    def test_extract_first_sentence_cuts_sentence_ending_with_ratio_numbers(self) -> None:
        text = "relacion 3:4. Otra cosa no relevante."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "relacion 3:4.")

    def test_extract_first_sentence_cuts_at_period_when_number_has_three_or_more_digits(
        self,
    ) -> None:
        text = "666. seis. Otra oracion."

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "666.")

    def test_extract_first_sentence_returns_entire_trimmed_text_when_no_punctuation(self) -> None:
        text = "   Texto sin puntuacion final   "

        result = self.extractor.extract_first_sentence(text)

        self.assertEqual(result, "Texto sin puntuacion final")

    def test_repeated_and_interleaved_calls_produce_identical_results(self) -> None:
        sample_a = "1. Primera oracion. Segunda."
        sample_b = "Texto con decimal 2.5 finalizado. Siguiente."

        result_a_first = self.extractor.extract_first_sentence(sample_a)
        result_b_first = self.extractor.extract_first_sentence(sample_b)
        result_a_second = self.extractor.extract_first_sentence(sample_a)
        result_b_second = self.extractor.extract_first_sentence(sample_b)

        self.assertEqual(result_a_first, result_a_second)
        self.assertEqual(result_b_first, result_b_second)
        self.assertEqual(result_a_first, "1. Primera oracion.")
        self.assertEqual(result_b_first, "Texto con decimal 2.5 finalizado.")
