from unittest import TestCase

from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.enums.quality_dimension import QualityDimension
from src.domain.quality.quality_response_parser import QualityResponseParser
from src.domain.tests.quality.feedback_fixtures import (
    FIXTURE_A_BULLET_SECTIONS_WEAKNESSES_SURVIVE,
    FIXTURE_B_NESTED_NUMBERED_SUB_LIST,
    FIXTURE_C_HORIZONTAL_RULE_WITH_TABLE,
    FIXTURE_D_COHERENCIA_ELLIPSIS_ITEM,
    FIXTURE_E_SAME_LEVEL_HEADING_ENDS_BLOCK,
    FIXTURE_F_MID_SENTENCE_BOLD_STAYS_INLINE,
    FIXTURE_G_MORE_THAN_EIGHT_ITEMS_SECTION,
    FIXTURE_H_GENERAL_SYNTHESIS_OVERWRITE_REGRESSION,
    FIXTURE_I_SONNET_STYLE_PLAIN_TITLES,
    FIXTURE_J_HAIKU_ID_60_PARAGRAPH_FLUSH_BULLETS,
    FIXTURE_K_GEMMA_STYLE_PLAIN_WEAKNESS_TITLE,
    FIXTURE_L_PLAIN_FORTALEZAS_DEBILIDADES_TITLES,
    FIXTURE_M_OPUS_ID_70_PARAGRAPH_FLUSH_BULLETS_WITH_SUB_BULLETS,
)

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
        self.assertEqual(result.scores[QualityDimension.CLARITY].feedback_blocks, ())

    def test_feedback_with_more_than_eight_items_in_section_is_capped(self):
        response = """**1. Claridad** [Puntuación: 8/10]
- Primera observación larga y descriptiva sobre claridad.
- Segunda observación también relevante sobre el texto.
- Tercera observación analítica complementaria.
- Cuarta observación que continúa la exposición analítica.
- Quinta observación que consolida la revisión de estilo.
- Sexta observación sobre precisión terminológica en el marco.
- Séptima observación sobre coherencia en los conceptos clave.
- Octava observación que cierra el límite de items.
- Novena observación descartada por superar el límite.
- Décima observación descartada por superar el límite.

**2. Coherencia** [Puntuación: 8/10]
Las ideas se conectan logicamente entre las distintas secciones del texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.CLARITY].feedback
        blocks = result.scores[QualityDimension.CLARITY].feedback_blocks
        self.assertEqual(len(blocks), 8)
        self.assertIn("Primera observación", feedback)
        self.assertIn("Segunda observación", feedback)
        self.assertIn("Tercera observación", feedback)
        self.assertIn("Cuarta observación", feedback)
        self.assertIn("Quinta observación", feedback)
        self.assertIn("Sexta observación", feedback)
        self.assertIn("Séptima observación", feedback)
        self.assertIn("Octava observación", feedback)
        self.assertNotIn("Novena observación", feedback)
        self.assertNotIn("Décima observación", feedback)

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
        self.assertIn("Análisis del Cierre:", feedback)
        self.assertIn("Síntesis Final:", feedback)
        self.assertNotIn("**Síntesis Final**", feedback)

    def test_dangling_bold_marker_removed_after_truncation(self):
        response = """**1. Argumentación** [Puntuación: 8/10]
Primera oración con **negrita que no cierra adecuadamente en esta parte.
Segunda oración que aporta contexto analítico complementario al análisis.
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

    def test_feedback_with_decimal_number_preserves_content_intact(self):
        response = """**1. Claridad** [Puntuación: 8/10]
Se evidencia una mejora de 1.5 puntos en la articulación expositiva general.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.CLARITY].feedback
        self.assertIn("mejora de 1.5 puntos", feedback)

    def test_feedback_with_initials_preserves_content_intact(self):
        response = """**1. Claridad** [Puntuación: 8/10]
El trabajo examina las ideas de A. R. Turing con profundidad conceptual relevante.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.CLARITY].feedback
        self.assertIn("A. R. Turing", feedback)

    def test_capped_feedback_with_numbered_bold_items_does_not_end_in_bare_list_number(
        self,
    ):
        response = """## **1. Argumentación** [Puntuación: 8/10]
### Fortalezas estructurales
El fragmento presenta una **argumentación sólida y bien jerarquizada** alrededor de tres mecanismos explicativos del razonamiento emergente:
1. **Composición estadística**: Se formula claramente (regularidades recombinadas a escala suficiente) y se cuestiona con evidencia contradictoria específica (BIG-Bench con 23 tareas que rompen el patrón suave esperado).
2. **Andamiaje implícito de cadena de pensamiento**: Se apoya en cadena causal clara (entrenamiento → representaciones procedimentales → activación por prompting) con predicciones falsables (densidad de ejemplos desarrollados correlaciona con emergencia pronunciada).
3. **Transiciones de fase representacionales**: Se ancla en analogía física rigurosa (cristalización como modelo de reorganización cualitativa) y se respalda con evidencia de interpretabilidad (Elhage et al., 2022 demostrando circuitos algorítmicos).
### Debilidades argumentativas
Síntesis superficial entre mecanismos que requiere mayor integración analítica en el texto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.ARGUMENTATION].feedback
        self.assertFalse(feedback.endswith(" 1."))
        self.assertFalse(feedback.endswith(" 2."))
        self.assertFalse(feedback.endswith(" 3."))
        self.assertIn("Composición estadística", feedback)

    def test_feedback_horizontal_rule_ends_block_and_ignores_subsequent_text(self):
        response = """## **2. Coherencia** [Puntuación: 8/10]
El texto mantiene coherencia lógica adecuada en sus secciones principales.
---
Observación final sobre el marco metodológico propuesto.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.COHERENCE].feedback
        self.assertNotIn("---", feedback)
        self.assertIn("El texto mantiene coherencia lógica adecuada", feedback)
        self.assertNotIn("Observación final sobre el marco", feedback)

    def test_feedback_strips_leading_blockquote_marker_and_preserves_quoted_text(self):
        response = """## **2. Conclusiones** [Puntuación: 6/10]
El texto no incluye una sección de conclusiones formal. El párrafo final termina con:
> "La investigación de interpretabilidad mecanicista ha proporcionado apoyo preliminar."
Evaluación del cierre presentado.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.CONCLUSIONS].feedback
        self.assertNotIn('> "', feedback)
        self.assertNotIn("> ", feedback)
        self.assertIn(
            '"La investigación de interpretabilidad mecanicista ha proporcionado apoyo preliminar."',
            feedback,
        )

    def test_feedback_horizontal_rule_variants_end_block(self):
        for rule in ("***", "___", "- - -"):
            response = f"""## **1. Claridad** [Puntuación: 8/10]
Primera observación sobre la claridad expositiva del manuscrito presentado.
{rule}
Segunda observación que debe ser ignorada por estar tras la regla horizontal.
"""
            parser = QualityResponseParser()
            result = parser.parse(response)
            feedback = result.scores[QualityDimension.CLARITY].feedback
            self.assertNotIn(rule, feedback)
            self.assertIn("Primera observación", feedback)
            self.assertNotIn("Segunda observación", feedback)

    def test_feedback_strips_blockquote_marker_without_following_space(self):
        response = """## **2. Conclusiones** [Puntuación: 6/10]
El texto no incluye una sección de conclusiones formal. El párrafo final termina con:
>"Cita en bloque sin espacio después del delimitador mayor que."
Evaluación del cierre presentado.
"""
        parser = QualityResponseParser()

        result = parser.parse(response)

        feedback = result.scores[QualityDimension.CONCLUSIONS].feedback
        self.assertNotIn(">", feedback)
        self.assertIn('"Cita en bloque sin espacio después del delimitador mayor que."', feedback)

    def test_fixture_bullet_sections_preserves_weaknesses_and_keeps_both_titles(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_A_BULLET_SECTIONS_WEAKNESSES_SURVIVE)
        clarity = result.scores[QualityDimension.CLARITY]
        self.assertEqual(clarity.score, 7.0)
        self.assertIn("Fortalezas:", clarity.feedback)
        self.assertIn("Problemas de claridad:", clarity.feedback)
        self.assertIn("El mensaje central está bien definido", clarity.feedback)
        self.assertIn("La definición de emergencia es técnica", clarity.feedback)
        self.assertNotIn("Párrafo adicional que debería descartarse", clarity.feedback)
        title_blocks = [b for b in clarity.feedback_blocks if b.kind == FeedbackBlockKind.TITLE]
        item_blocks = [b for b in clarity.feedback_blocks if b.kind == FeedbackBlockKind.ITEM]
        self.assertEqual(len(title_blocks), 2)
        self.assertEqual(len(item_blocks), 11)

    def test_fixture_nested_numbered_sub_list_keeps_nested_items_without_counting_them(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_B_NESTED_NUMBERED_SUB_LIST)
        argumentation = result.scores[QualityDimension.ARGUMENTATION]
        self.assertEqual(argumentation.score, 8.0)
        self.assertIn("Fortalezas:", argumentation.feedback)
        self.assertIn("Debilidades:", argumentation.feedback)
        self.assertIn("Composición estadística", argumentation.feedback)
        self.assertIn("Andamiaje implícito", argumentation.feedback)
        self.assertIn("Transiciones de fase", argumentation.feedback)
        self.assertNotIn("Noveno item descartable", argumentation.feedback)
        nested_items = [b for b in argumentation.feedback_blocks if b.level == 1]
        self.assertEqual(len(nested_items), 3)

    def test_fixture_horizontal_rule_drops_everything_after_rule_including_table(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_C_HORIZONTAL_RULE_WITH_TABLE)
        conclusions = result.scores[QualityDimension.CONCLUSIONS]
        self.assertEqual(conclusions.score, 6.0)
        self.assertIn("Estado Actual:", conclusions.feedback)
        self.assertIn("Lo que Infiero del Contenido Final:", conclusions.feedback)
        self.assertNotIn("Síntesis Evaluativa", conclusions.feedback)
        self.assertNotIn("Recomendación editorial", conclusions.feedback)
        self.assertNotIn("Argumentación | 8/10", conclusions.feedback)

    def test_fixture_coherencia_ellipsis_item_stays_whole_without_cutting(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_D_COHERENCIA_ELLIPSIS_ITEM)
        coherence = result.scores[QualityDimension.COHERENCE]
        self.assertEqual(coherence.score, 7.0)
        expected_ellipsis_text = (
            'Las transiciones intraseccionales (ej: "En primer lugar... En segundo '
            'lugar... En tercer lugar") son claras y efectivas.'
        )
        self.assertIn(expected_ellipsis_text, coherence.feedback)

    def test_fixture_same_level_heading_ends_dimension_block(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_E_SAME_LEVEL_HEADING_ENDS_BLOCK)
        clarity = result.scores[QualityDimension.CLARITY]
        self.assertEqual(clarity.score, 7.0)
        self.assertIn("El objetivo general del estudio", clarity.feedback)
        self.assertNotIn("Observación final (meta)", clarity.feedback)
        self.assertNotIn("Este párrafo de nivel dos", clarity.feedback)

    def test_fixture_mid_sentence_bold_stays_inline(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_F_MID_SENTENCE_BOLD_STAYS_INLINE)
        clarity = result.scores[QualityDimension.CLARITY]
        self.assertEqual(clarity.score, 8.0)
        self.assertIn("**claridad conceptual excelente**", clarity.feedback)
        self.assertEqual(len(clarity.feedback_blocks), 1)
        self.assertEqual(clarity.feedback_blocks[0].kind, FeedbackBlockKind.TEXT)

    def test_fixture_more_than_eight_items_keeps_first_eight_whole(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_G_MORE_THAN_EIGHT_ITEMS_SECTION)
        argumentation = result.scores[QualityDimension.ARGUMENTATION]
        self.assertEqual(argumentation.score, 8.0)
        self.assertIn("Primer argumento", argumentation.feedback)
        self.assertIn("Segundo argumento", argumentation.feedback)
        self.assertIn("Tercer argumento", argumentation.feedback)
        self.assertIn("Cuarto argumento", argumentation.feedback)
        self.assertIn("Quinto argumento", argumentation.feedback)
        self.assertIn("Sexto argumento", argumentation.feedback)
        self.assertIn("Séptimo argumento", argumentation.feedback)
        self.assertIn("Octavo argumento", argumentation.feedback)
        self.assertNotIn("Noveno argumento", argumentation.feedback)
        self.assertNotIn("Décimo argumento", argumentation.feedback)
        item_blocks = [b for b in argumentation.feedback_blocks if b.kind == FeedbackBlockKind.ITEM]
        self.assertEqual(len(item_blocks), 8)

    def test_fixture_response_fifty_five_general_synthesis_does_not_overwrite_parsed_dimensions(
        self,
    ):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_H_GENERAL_SYNTHESIS_OVERWRITE_REGRESSION)

        argumentation = result.scores[QualityDimension.ARGUMENTATION]
        self.assertEqual(argumentation.score, 8.0)
        self.assertNotEqual(argumentation.feedback, "No disponible")
        self.assertIn("Fortalezas:", argumentation.feedback)
        self.assertIn("Debilidades:", argumentation.feedback)
        argumentation_titles = [
            block.text
            for block in argumentation.feedback_blocks
            if block.kind == FeedbackBlockKind.TITLE
        ]
        self.assertIn("Fortalezas", argumentation_titles)
        self.assertIn("Debilidades", argumentation_titles)
        argumentation_items = [
            block for block in argumentation.feedback_blocks if block.kind == FeedbackBlockKind.ITEM
        ]
        self.assertGreater(len(argumentation_items), 0)

        conclusions = result.scores[QualityDimension.CONCLUSIONS]
        self.assertEqual(conclusions.score, 6.0)
        self.assertNotEqual(conclusions.feedback, "No disponible")
        conclusions_titles = [
            block.text
            for block in conclusions.feedback_blocks
            if block.kind == FeedbackBlockKind.TITLE
        ]
        self.assertIn(
            "Análisis del párrafo final (Transiciones de fase representacionales)",
            conclusions_titles,
        )
        conclusions_items = [
            block for block in conclusions.feedback_blocks if block.kind == FeedbackBlockKind.ITEM
        ]
        self.assertGreater(len(conclusions_items), 0)

    def test_empty_trailing_block_does_not_erase_parsed_dimension(self):
        response = """## **1. Argumentación** [Puntuación: 8/10]
**Fortalezas:**
- Presenta argumentos sólidos y estructurados a lo largo del manuscrito.

## **Argumentación**
"""
        parser = QualityResponseParser()
        result = parser.parse(response)

        argumentation = result.scores[QualityDimension.ARGUMENTATION]
        self.assertEqual(argumentation.score, 8.0)
        self.assertNotEqual(argumentation.feedback, "No disponible")
        self.assertIn("Fortalezas:", argumentation.feedback)
        self.assertGreater(len(argumentation.feedback_blocks), 0)

    def test_later_block_with_content_overwrites_earlier_empty_default(self):
        response = """## **Argumentación**

## **1. Argumentación** [Puntuación: 8/10]
**Fortalezas:**
- Presenta argumentos sólidos y estructurados a lo largo del manuscrito.
"""
        parser = QualityResponseParser()
        result = parser.parse(response)

        argumentation = result.scores[QualityDimension.ARGUMENTATION]
        self.assertEqual(argumentation.score, 8.0)
        self.assertNotEqual(argumentation.feedback, "No disponible")
        self.assertIn("Fortalezas:", argumentation.feedback)
        self.assertGreater(len(argumentation.feedback_blocks), 0)

    def test_sonnet_style_response_weaknesses_survive_and_cap_of_eight_applies(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_I_SONNET_STYLE_PLAIN_TITLES)
        clarity = result.scores[QualityDimension.CLARITY]

        self.assertEqual(clarity.score, 8.0)
        self.assertIn("Lo que funciona bien:", clarity.feedback)
        self.assertIn("Lo que necesita mejorar:", clarity.feedback)
        self.assertIn("Octavo aspecto débil", clarity.feedback)
        self.assertNotIn("Noveno aspecto débil", clarity.feedback)

        titles = [b.text for b in clarity.feedback_blocks if b.kind == FeedbackBlockKind.TITLE]
        self.assertIn("Lo que funciona bien", titles)
        self.assertIn("Lo que necesita mejorar", titles)

        improving_items = [
            b
            for b in clarity.feedback_blocks
            if b.kind == FeedbackBlockKind.ITEM and "aspecto débil" in b.text
        ]
        self.assertEqual(len(improving_items), 8)

    def test_opus_id_70_fixture_preserves_two_level_hierarchy_under_cap_eight(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_M_OPUS_ID_70_PARAGRAPH_FLUSH_BULLETS_WITH_SUB_BULLETS)
        argumentation = result.scores[QualityDimension.ARGUMENTATION]

        self.assertEqual(argumentation.score, 6.0)
        level_zero_items = [
            b
            for b in argumentation.feedback_blocks
            if b.level == 0 and b.kind == FeedbackBlockKind.ITEM
        ]
        level_one_items = [b for b in argumentation.feedback_blocks if b.level == 1]

        self.assertEqual(len(level_zero_items), 6)
        self.assertEqual(len(level_one_items), 7)
        self.assertIn("Contradicción numérica sin resolver", argumentation.feedback)
        self.assertIn("Bai et al.", argumentation.feedback)

    def test_haiku_sixty_style_flush_bullets_survive_as_children_and_subsequent_paragraphs_kept(
        self,
    ):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_J_HAIKU_ID_60_PARAGRAPH_FLUSH_BULLETS)
        argumentation = result.scores[QualityDimension.ARGUMENTATION]

        self.assertEqual(argumentation.score, 8.0)
        self.assertIn("Composición estadística parsimoniosa", argumentation.feedback)
        self.assertIn("Andamiaje implícito de cadena", argumentation.feedback)
        self.assertIn("Transiciones de fase representacionales", argumentation.feedback)
        self.assertIn("Identificación de tensiones teóricas", argumentation.feedback)

        children = [
            b
            for b in argumentation.feedback_blocks
            if b.level == 0 and b.kind == FeedbackBlockKind.ITEM
        ]
        self.assertEqual(len(children), 3)

    def test_gemma_style_weakness_section_survives_as_title_with_single_bullet(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_K_GEMMA_STYLE_PLAIN_WEAKNESS_TITLE)
        clarity = result.scores[QualityDimension.CLARITY]

        self.assertEqual(clarity.score, 9.0)
        self.assertIn("Lo que funciona muy bien:", clarity.feedback)
        self.assertIn("Lo que podría mejorar:", clarity.feedback)
        self.assertIn("La transición hacia las transiciones de fase", clarity.feedback)

        titles = [b.text for b in clarity.feedback_blocks if b.kind == FeedbackBlockKind.TITLE]
        self.assertIn("Lo que funciona muy bien", titles)
        self.assertIn("Lo que podría mejorar", titles)

    def test_plain_fortalezas_and_debilidades_titles_both_parsed_as_titles(self):
        parser = QualityResponseParser()
        result = parser.parse(FIXTURE_L_PLAIN_FORTALEZAS_DEBILIDADES_TITLES)
        argumentation = result.scores[QualityDimension.ARGUMENTATION]

        self.assertEqual(argumentation.score, 7.0)
        self.assertIn("Fortalezas:", argumentation.feedback)
        self.assertIn("Debilidades:", argumentation.feedback)

        titles = [
            b.text for b in argumentation.feedback_blocks if b.kind == FeedbackBlockKind.TITLE
        ]
        self.assertEqual(titles, ["Fortalezas", "Debilidades"])
