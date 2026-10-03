from unittest import TestCase

from src.domain.enums.quality_dimension import QualityDimension
from src.domain.quality.quality_response_parser import QualityResponseParser

VALID_RESPONSE_TWO = """**1. Argumentación** [Puntuación: 8/10]
Los argumentos presentados son solidos y estan bien fundamentados.

**2. Conclusiones** [Puntuación: 8/10]
Las conclusiones se desprenden claramente del contenido desarrollado.
"""


class TestQualityResponseParser(TestCase):
    def test_numbered_and_unnumbered_headers_both_parse_to_same_score(self):
        numbered_response = """**1. Claridad** [Puntuación: 8/10]
Texto de retroalimentacion suficientemente largo para superar el minimo.
"""
        unnumbered_response = """**Claridad** [Puntuación: 8/10]
Texto de retroalimentacion suficientemente largo para superar el minimo.
"""
        parser = QualityResponseParser()

        result_numbered = parser.parse(numbered_response)
        result_unnumbered = parser.parse(unnumbered_response)

        self.assertEqual(result_numbered.scores[QualityDimension.CLARITY].score, 8.0)
        self.assertEqual(result_unnumbered.scores[QualityDimension.CLARITY].score, 8.0)

    def test_score_inferred_from_narrative_when_explicit_score_absent(self):
        response = """**1. Claridad**
El argumento es bastante bueno y adecuado en su desarrollo general del tema.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].score, 7.5)

    def test_excelente_keyword_infers_eight_point_five(self):
        response = """**1. Claridad**
El trabajo es excelente y sobresaliente en su desarrollo argumentativo general.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].score, 8.5)

    def test_aceptable_keyword_infers_six_point_zero(self):
        response = """**1. Claridad**
El trabajo resulta aceptable y suficiente en su desarrollo argumentativo general.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].score, 6.0)

    def test_deficiente_keyword_infers_four_point_zero(self):
        response = """**1. Claridad**
El trabajo resulta deficiente y debil en su desarrollo argumentativo general.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].score, 4.0)

    def test_no_keyword_match_uses_neutral_default_score(self):
        response = """**1. Claridad**
Este texto no contiene ninguna palabra clave narrativa reconocida en absoluto.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].score, 7.0)

    def test_feedback_shorter_than_ten_characters_becomes_neutral_default(self):
        response = """**1. Claridad** [Puntuación: 8/10]
Corto.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].feedback, "No disponible")

    def test_feedback_longer_than_three_sentences_is_truncated(self):
        response = """**1. Claridad** [Puntuación: 8/10]
Primera oracion larga y descriptiva. Segunda oracion tambien larga. Tercera oracion mas. Cuarta oracion final. Quinta oracion sobrante.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.CLARITY].feedback
        sentence_count = len([s for s in feedback.split(".") if s.strip()])
        self.assertEqual(sentence_count, 3)
        self.assertTrue(feedback.endswith("."))

    def test_argumentacion_block_is_not_misclassified_as_claridad(self):
        response = """**1. Argumentación** [Puntuación: 8/10]
La argumentacion presenta un argumento solido y bien fundamentado en el texto.

**2. Conclusiones** [Puntuación: 8/10]
Las conclusiones se desprenden claramente del contenido desarrollado.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(
            result.scores[QualityDimension.ARGUMENTATION].feedback,
            "La argumentacion presenta un argumento solido y bien fundamentado en el texto.",
        )

    def test_markdown_list_markers_are_stripped_from_feedback(self):
        response = """**1. Argumentación** [Puntuación: 8/10]
* El autor identifica tres explicaciones mecanicistas del razonamiento emergente.
+ Es un buen resumen del trabajo de los autores en general.

**2. Conclusiones** [Puntuación: 8/10]
Las conclusiones se desprenden claramente del contenido desarrollado.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.ARGUMENTATION].feedback
        self.assertFalse(feedback.startswith("*"))
        self.assertNotIn("+ Es un buen resumen", feedback)
        self.assertIn("El autor identifica tres explicaciones mecanicistas", feedback)

    def test_one_missing_dimension_in_otherwise_valid_response_keeps_the_rest(self):
        response = """**1. Claridad** [Puntuación: 8/10]
El argumento central es claro y facil de seguir en todo el texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].score, 8.0)
        self.assertEqual(result.scores[QualityDimension.COHERENCE].score, 7.0)
        self.assertEqual(result.scores[QualityDimension.COHERENCE].feedback, "No disponible")
        self.assertEqual(
            result.matched_dimensions,
            frozenset({QualityDimension.CLARITY}),
        )

    def test_markdown_heading_two_with_mid_sentence_bold_in_conclusions_preserves_argumentation(
        self,
    ):
        response = """## **1. Argumentación** [Puntuación: 7/10]
Los argumentos presentados demuestran un desarrollo lógico y riguroso a lo largo del texto.

## **2. Conclusiones** [Puntuación: 4/10]
### Análisis del Cierre
Las conclusiones resultan parciales e insuficientes respecto a los objetivos iniciales.
### **Síntesis Final**
El fragmento evidencia **argumentación académica rigurosa pero incompleta**. La arquitectura lógica general necesita mayor solidez en el desenlace.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.ARGUMENTATION].score, 7.0)
        self.assertNotEqual(result.scores[QualityDimension.ARGUMENTATION].feedback, "No disponible")
        self.assertIn(
            "Los argumentos presentados demuestran un desarrollo lógico",
            result.scores[QualityDimension.ARGUMENTATION].feedback,
        )
        self.assertEqual(result.scores[QualityDimension.CONCLUSIONS].score, 4.0)

    def test_bold_phrase_starting_with_dimension_word_mid_line_does_not_split(self):
        response = """**1. Claridad** [Puntuación: 8/10]
El texto mantiene una **claridad conceptual excelente** durante toda la exposición teórica.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        self.assertEqual(result.scores[QualityDimension.CLARITY].score, 8.0)
        self.assertIn(
            "El texto mantiene una **claridad conceptual excelente**",
            result.scores[QualityDimension.CLARITY].feedback,
        )

    def test_markdown_heading_markers_removed_from_feedback_lines(self):
        response = """**1. Argumentación** [Puntuación: 8/10]
### Análisis del Cierre
Los argumentos están adecuadamente desarrollados y fundamentados con evidencia.
### **Síntesis Final**
Se observa una articulación consistente entre las premisas y el desarrollo.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.ARGUMENTATION].feedback
        self.assertNotIn("###", feedback)
        self.assertIn("Análisis del Cierre", feedback)
        self.assertIn("**Síntesis Final**", feedback)

    def test_dangling_bold_marker_removed_after_truncation(self):
        response = """**1. Argumentación** [Puntuación: 8/10]
Primera oración con **negrita que no cierra adecuadamente en esta parte. Segunda oración que aporta contexto analítico complementario. Tercera oración para completar el límite de oraciones. Cuarta oración descartada con el cierre.**
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.ARGUMENTATION].feedback
        self.assertEqual(feedback.count("**") % 2, 0)
        self.assertNotIn("**negrita que no cierra", feedback)
        self.assertIn("negrita que no cierra", feedback)

    def test_dangling_bold_marker_removed_from_unpaired_feedback(self):
        response = """**1. Argumentación** [Puntuación: 8/10]
Esta retroalimentación contiene una marca **huérfana sin par de cierre.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.ARGUMENTATION].feedback
        self.assertEqual(feedback.count("**"), 0)
        self.assertNotIn("**", feedback)

    def test_claude_coherencia_response_preserves_citations_with_et_al_intact(self):
        response = """## **2. Coherencia** [Puntuación: 8/10]
### Fortalezas
- **Progresión lógica dentro de secciones**: La transición entre las hipótesis mecanicistas fluye naturalmente de lo más simple a lo más sofisticado.
- **Respaldo empírico incorporado**: Cada hipótesis se ancla inmediatamente con citas (Wei et al., 2022; Elhage et al., 2022), reforzando credibilidad sin interrumpir la narrativa.
- **Cierre de loops conceptuales**: La discusión regresa coherentemente a la idea de capacidades latentes.
### Áreas de mejora
- **Transición débil**: Entre el párrafo y el primero falta un puente.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.COHERENCE].feedback
        self.assertIn("(Wei et al., 2022; Elhage et al., 2022)", feedback)
        self.assertFalse(feedback.endswith("et al."))
        self.assertNotIn("al. ,", feedback)

    def test_feedback_with_decimal_number_is_not_split(self):
        response = """**1. Claridad** [Puntuación: 8/10]
Se evidencia una mejora de 1.5 puntos en la articulación expositiva general. Segunda oración explicativa. Tercera oración descriptiva. Cuarta oración descartable.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.CLARITY].feedback
        self.assertIn("mejora de 1.5 puntos", feedback)
        self.assertIn("Tercera oración descriptiva.", feedback)
        self.assertNotIn("Cuarta oración", feedback)

    def test_feedback_with_initials_is_not_split(self):
        response = """**1. Claridad** [Puntuación: 8/10]
El trabajo examina las ideas de A. R. Turing con profundidad conceptual. Segunda oración analítica sobre el contenido. Tercera oración de síntesis relevante. Cuarta oración descartable.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.CLARITY].feedback
        self.assertIn("A. R. Turing", feedback)
        self.assertIn("Tercera oración de síntesis", feedback)
        self.assertNotIn("Cuarta oración", feedback)
