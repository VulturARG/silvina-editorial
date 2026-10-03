from unittest import TestCase

from src.domain.quality.sentence_splitter import SentenceSplitter


class TestSentenceSplitter(TestCase):
    def test_split_empty_text_returns_empty_list(self):
        splitter = SentenceSplitter()

        sentences = splitter.split("")

        self.assertEqual(sentences, [])

    def test_split_single_sentence_returns_single_element_list(self):
        splitter = SentenceSplitter()

        sentences = splitter.split("La propuesta metodológica es sólida.")

        self.assertEqual(sentences, ["La propuesta metodológica es sólida."])

    def test_split_multiple_sentences_separated_by_period(self):
        splitter = SentenceSplitter()

        sentences = splitter.split("Primera oración. Segunda oración. Tercera oración.")

        self.assertEqual(
            sentences,
            ["Primera oración.", "Segunda oración.", "Tercera oración."],
        )

    def test_split_multiple_sentences_with_exclamation_and_question_marks(self):
        splitter = SentenceSplitter()

        sentences = splitter.split("¡Excelente trabajo! ¿Es suficiente la evidencia? Sí, lo es.")

        self.assertEqual(
            sentences,
            ["¡Excelente trabajo!", "¿Es suficiente la evidencia?", "Sí, lo es."],
        )

    def test_split_does_not_break_on_decimal_number(self):
        splitter = SentenceSplitter()

        sentences = splitter.split(
            "Se observa una mejora de 1.5 puntos en la escala. La progresión es adecuada."
        )

        self.assertEqual(
            sentences,
            [
                "Se observa una mejora de 1.5 puntos en la escala.",
                "La progresión es adecuada.",
            ],
        )

    def test_split_does_not_break_on_single_capital_letter_initials(self):
        splitter = SentenceSplitter()

        sentences = splitter.split(
            "El postulado de A. R. Turing es fundamental. La demostración fue confirmada."
        )

        self.assertEqual(
            sentences,
            [
                "El postulado de A. R. Turing es fundamental.",
                "La demostración fue confirmada.",
            ],
        )

    def test_split_does_not_break_on_known_abbreviations(self):
        splitter = SentenceSplitter()

        sentences = splitter.split(
            "Según Wei et al. El Dr. Gómez y la Dra. Pérez en el vol. 1, ed. 2, "
            "véase p. 10 y pp. 20-25 (cf. Fig. 3 y otros, etc. y p. ej. Casos de estudio). "
            "La síntesis finaliza aquí."
        )

        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[1], "La síntesis finaliza aquí.")

    def test_split_preserves_next_sentence_starting_with_inverted_marks_quotes_parentheses_or_asterisk(
        self,
    ):
        splitter = SentenceSplitter()

        sentences = splitter.split(
            "Primera oración. ¿Segunda oración? ¡Tercera oración! "
            "**Cuarta oración en negrita**. (Quinta oración entre paréntesis)."
        )

        self.assertEqual(len(sentences), 5)
        self.assertEqual(sentences[0], "Primera oración.")
        self.assertEqual(sentences[1], "¿Segunda oración?")
        self.assertEqual(sentences[2], "¡Tercera oración!")
        self.assertEqual(sentences[3], "**Cuarta oración en negrita**.")
        self.assertEqual(sentences[4], "(Quinta oración entre paréntesis).")

    def test_cap_sentences_returns_text_as_is_when_count_within_limit(self):
        splitter = SentenceSplitter()
        text = "Primera oración. Segunda oración."

        capped = splitter.cap_sentences(text, maximum_sentences=3)

        self.assertEqual(capped, text)

    def test_cap_sentences_truncates_at_limit_preserving_natural_punctuation(self):
        splitter = SentenceSplitter()
        text = (
            "Primera oración. Segunda oración con desarrollo. "
            "Tercera oración concluyente. Cuarta oración excluida. Quinta oración sobrante."
        )

        capped = splitter.cap_sentences(text, maximum_sentences=3)

        self.assertEqual(
            capped,
            "Primera oración. Segunda oración con desarrollo. Tercera oración concluyente.",
        )

    def test_cap_sentences_preserves_full_citation_with_et_al(self):
        splitter = SentenceSplitter()
        text = (
            "Fortalezas **Progresión lógica dentro de secciones**: La transición fluye naturalmente. "
            "**Respaldo empírico incorporado**: Cada hipótesis se ancla inmediatamente con citas "
            "(Wei et al., 2022; Elhage et al., 2022), reforzando credibilidad sin interrumpir la narrativa. "
            "**Cierre de loops conceptuales**: La discusión regresa coherentemente. "
            "Áreas de mejora **Transición débil**: Falta un puente."
        )

        capped = splitter.cap_sentences(text, maximum_sentences=3)

        self.assertIn("(Wei et al., 2022; Elhage et al., 2022)", capped)
        self.assertFalse(capped.endswith("et al."))
        self.assertTrue(capped.endswith("La discusión regresa coherentemente."))
