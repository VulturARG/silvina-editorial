from unittest import TestCase

from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.quality.feedback_structure_parser import FeedbackStructureParser
from src.domain.tests.quality.feedback_fixtures import (
    FIXTURE_B_NESTED_NUMBERED_SUB_LIST,
    FIXTURE_M_OPUS_ID_70_PARAGRAPH_FLUSH_BULLETS_WITH_SUB_BULLETS,
)


class TestFeedbackStructureParser(TestCase):
    def test_title_from_heading_line_removes_hashes_wrapping_bold_and_trailing_colon(self):
        lines = [
            "### **Fortalezas:**",
            "- Primer punto relevante",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=2)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Fortalezas")
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[0].marker, "")

    def test_title_from_bold_only_line_with_trailing_colon(self):
        lines = [
            "**Debilidades:**",
            "- Primer punto débil identificado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Debilidades")

    def test_title_from_bold_only_line_with_colon_outside_bold(self):
        lines = [
            "**Nota sobre estructura general**:",
            "Observación detallada sobre el esquema expositivo general.",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Nota sobre estructura general")

    def test_label_bold_at_start_of_line_is_not_title(self):
        lines = [
            "**Punto clave**: este es un texto explicativo continuo en el párrafo.",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(
            blocks[0].text,
            "**Punto clave**: este es un texto explicativo continuo en el párrafo.",
        )

    def test_mid_sentence_bold_phrase_is_not_title(self):
        lines = [
            "El texto exhibe una **claridad conceptual excelente** en su desarrollo.",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(
            blocks[0].text,
            "El texto exhibe una **claridad conceptual excelente** en su desarrollo.",
        )

    def test_bullet_items_with_dash_star_and_plus_get_bullet_marker(self):
        lines = [
            "- Primer elemento con guión",
            "* Segundo elemento con asterisco",
            "+ Tercer elemento con signo más",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        for block in blocks:
            self.assertEqual(block.kind, FeedbackBlockKind.ITEM)
            self.assertEqual(block.marker, "•")
            self.assertEqual(block.level, 0)
        self.assertEqual(blocks[0].text, "Primer elemento con guión")
        self.assertEqual(blocks[1].text, "Segundo elemento con asterisco")
        self.assertEqual(blocks[2].text, "Tercer elemento con signo más")

    def test_numbered_items_get_original_number_marker(self):
        lines = [
            "1. Primer punto ordenado",
            "2. Segundo punto ordenado",
            "10. Décimo punto ordenado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].marker, "1.")
        self.assertEqual(blocks[0].text, "Primer punto ordenado")
        self.assertEqual(blocks[1].marker, "2.")
        self.assertEqual(blocks[1].text, "Segundo punto ordenado")
        self.assertEqual(blocks[2].marker, "10.")
        self.assertEqual(blocks[2].text, "Décimo punto ordenado")

    def test_nested_item_indented_deeper_than_previous_top_level_item_has_level_one(self):
        lines = [
            "- Elemento principal",
            "  1. Sub-elemento numerado anidado",
            "  - Sub-elemento viñeta anidado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[0].marker, "•")
        self.assertEqual(blocks[1].level, 1)
        self.assertEqual(blocks[1].marker, "1.")
        self.assertEqual(blocks[1].text, "Sub-elemento numerado anidado")
        self.assertEqual(blocks[2].level, 1)
        self.assertEqual(blocks[2].marker, "•")
        self.assertEqual(blocks[2].text, "Sub-elemento viñeta anidado")

    def test_nested_items_are_not_counted_toward_section_cap_and_kept_with_parent(self):
        lines = [
            "- Primer elemento principal",
            "- Segundo elemento principal con hijos:",
            "  1. Primer sub-elemento",
            "  2. Segundo sub-elemento",
            "- Tercer elemento principal",
            "- Cuarto elemento principal descartable",
        ]
        parser = FeedbackStructureParser(maximum_items_per_section=3)
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 5)
        self.assertEqual(blocks[0].text, "Primer elemento principal")
        self.assertEqual(blocks[1].text, "Segundo elemento principal con hijos:")
        self.assertEqual(blocks[2].text, "Primer sub-elemento")
        self.assertEqual(blocks[2].level, 1)
        self.assertEqual(blocks[3].text, "Segundo sub-elemento")
        self.assertEqual(blocks[3].level, 1)
        self.assertEqual(blocks[4].text, "Tercer elemento principal")

    def test_nested_items_of_dropped_parent_are_also_dropped(self):
        lines = [
            "- Primer elemento",
            "- Segundo elemento",
            "- Tercer elemento",
            "- Cuarto elemento que se descartará:",
            "  1. Sub-elemento del padre descartado",
        ]
        parser = FeedbackStructureParser(maximum_items_per_section=3)
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertNotIn("Sub-elemento del padre descartado", [b.text for b in blocks])

    def test_horizontal_rule_ends_block_and_ignores_subsequent_lines(self):
        lines = [
            "**Fortalezas:**",
            "- Elemento visible previo a la regla horizontal",
            "---",
            "**Debilidades:**",
            "- Elemento que debe ser completamente ignorado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].text, "Fortalezas")
        self.assertEqual(blocks[1].text, "Elemento visible previo a la regla horizontal")

    def test_heading_level_less_than_or_equal_to_dimension_heading_level_ends_block(self):
        lines = [
            "### Observaciones",
            "- Comentario sobre la dimensión analizada",
            "## Observación final (meta)",
            "- Contenido posterior a la cabecera del mismo nivel",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=2)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].text, "Observaciones")
        self.assertEqual(blocks[1].text, "Comentario sobre la dimensión analizada")

    def test_heading_level_greater_than_dimension_heading_level_is_parsed_as_title(self):
        lines = [
            "### Observaciones específicas",
            "- Comentario detallado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=2)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Observaciones específicas")

    def test_table_lines_starting_with_pipe_are_dropped(self):
        lines = [
            "### Evaluación",
            "| Columna 1 | Columna 2 |",
            "|-----------|-----------|",
            "| Dato 1    | Dato 2    |",
            "- Comentario evaluativo legítimo",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].text, "Evaluación")
        self.assertEqual(blocks[1].text, "Comentario evaluativo legítimo")

    def test_leading_blockquote_marker_is_stripped(self):
        lines = [
            '> "Esta es una cita textual relevante incluida en el análisis."',
            '>"Esta es otra cita sin espacio después del delimitador."',
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(
            blocks[0].text,
            '"Esta es una cita textual relevante incluida en el análisis."',
        )
        self.assertEqual(
            blocks[1].text,
            '"Esta es otra cita sin espacio después del delimitador."',
        )

    def test_dangling_unpaired_bold_removed_while_paired_bold_is_kept(self):
        lines = [
            "- Texto con **negrita huérfana sin cierre",
            "- Texto con **negrita cerrada correctamente** en el cuerpo",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].text, "Texto con negrita huérfana sin cierre")
        self.assertEqual(blocks[1].text, "Texto con **negrita cerrada correctamente** en el cuerpo")

    def test_blank_lines_are_dropped(self):
        lines = [
            "",
            "   ",
            "- Elemento único rodeado de líneas vacías",
            "",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].text, "Elemento único rodeado de líneas vacías")

    def test_title_whose_section_has_no_items_is_dropped(self):
        lines = [
            "### Fortalezas",
            "- Elemento presente",
            "### Debilidades",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].text, "Fortalezas")
        self.assertEqual(blocks[1].text, "Elemento presente")
        self.assertNotIn("Debilidades", [b.text for b in blocks])

    def test_consecutive_titles_drops_title_with_no_items(self):
        lines = [
            "### Encabezado intermedio vacío",
            "**Debilidades secundarias:**",
            "- Primer punto de debilidad",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].text, "Debilidades secundarias")
        self.assertEqual(blocks[1].text, "Primer punto de debilidad")

    def test_blocks_before_first_title_form_initial_section(self):
        lines = [
            "Texto introductorio antes del primer título formal.",
            "- Viñeta previa",
            "**Fortalezas:**",
            "- Viñeta posterior",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 4)
        self.assertEqual(blocks[0].text, "Texto introductorio antes del primer título formal.")
        self.assertEqual(blocks[1].text, "Viñeta previa")
        self.assertEqual(blocks[2].text, "Fortalezas")
        self.assertEqual(blocks[3].text, "Viñeta posterior")

    def test_default_maximum_items_per_section_is_eight(self):
        lines = [
            "- Primer elemento",
            "- Segundo elemento",
            "- Tercer elemento",
            "- Cuarto elemento",
            "- Quinto elemento",
            "- Sexto elemento",
            "- Séptimo elemento",
            "- Octavo elemento",
            "- Noveno elemento descartable",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 8)
        self.assertEqual(blocks[7].text, "Octavo elemento")

    def test_plain_line_ending_in_colon_under_sixty_chars_followed_by_list_is_title(self):
        lines = [
            "Lo que funciona bien:",
            "- Primer aspecto positivo",
            "- Segundo aspecto positivo",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Lo que funciona bien")
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].level, 0)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].level, 0)

    def test_plain_line_ending_in_colon_with_sentence_punctuation_is_not_title(self):
        lines = [
            "Párrafo 1. Observaciones principales:",
            "- Primer elemento listado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[0].text, "Párrafo 1. Observaciones principales:")

    def test_plain_line_ending_in_colon_longer_than_sixty_chars_is_not_title(self):
        long_line = (
            "A lo largo de la exposición teórica del manuscrito se evidencian múltiples "
            "aspectos críticos:"
        )
        lines = [
            long_line,
            "- Primer elemento listado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[0].text, long_line)

    def test_plain_line_ending_in_colon_not_followed_by_list_is_not_title(self):
        lines = [
            "Aspectos a considerar en el análisis:",
            "Este es un párrafo de texto normal que continúa la explicación sin lista.",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[0].text, "Aspectos a considerar en el análisis:")
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.TEXT)

    def test_unindented_flush_bullets_under_paragraph_ending_in_colon_become_children_level_one(
        self,
    ):
        lines = [
            (
                "**Síntesis de mecanismos**: Los autores presentan tres hipótesis "
                "competentes sin privilegiar una:"
            ),
            "- Composición estadística parsimoniosa pero insuficiente",
            "- Andamiaje implícito de cadena de pensamiento sensible",
            "- Transiciones de fase representacionales con evidencia",
            "",
            "Cada una se presenta con su base empírica y limitaciones correspondientes.",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 5)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].level, 1)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].level, 1)
        self.assertEqual(blocks[3].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[3].level, 1)
        self.assertEqual(blocks[4].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[4].level, 0)

    def test_plain_titles_with_weaknesses_survive_as_sections_with_items(self):
        lines = [
            "Lo que funciona bien:",
            "- Fortaleza uno",
            "- Fortaleza dos",
            "",
            "Lo que necesita mejorar:",
            "- Debilidad uno",
            "- Debilidad dos",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 6)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Lo que funciona bien")
        self.assertEqual(blocks[1].text, "Fortaleza uno")
        self.assertEqual(blocks[2].text, "Fortaleza dos")
        self.assertEqual(blocks[3].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[3].text, "Lo que necesita mejorar")
        self.assertEqual(blocks[4].text, "Debilidad uno")
        self.assertEqual(blocks[5].text, "Debilidad dos")

    def test_bullet_item_ending_in_colon_followed_by_flush_bullets_makes_them_children_level_one(
        self,
    ):
        lines = [
            "- **Etiqueta principal**:",
            "- Primer aspecto derivado",
            "- Segundo aspecto derivado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].level, 1)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].level, 1)

    def test_numbered_item_ending_in_colon_followed_by_flush_items_makes_them_children_level_one(
        self,
    ):
        lines = [
            "1. **Etiqueta principal**:",
            "1. Primer aspecto derivado",
            "2. Segundo aspecto derivado",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[0].marker, "1.")
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].level, 1)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].level, 1)

    def test_bullet_item_ending_in_colon_followed_by_more_indented_list_handled_as_nested_rule(
        self,
    ):
        lines = [
            "- Viñeta principal:",
            "  - Primer sub-elemento más indentado",
            "  - Segundo sub-elemento más indentado",
            "- Siguiente elemento al nivel principal",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 4)
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[1].level, 1)
        self.assertEqual(blocks[2].level, 1)
        self.assertEqual(blocks[3].level, 0)

    def test_children_mode_resets_at_next_non_list_line(self):
        lines = [
            "A lo largo de la exposición se identifican diversos aspectos críticos:",
            "- Hijo dependiente uno",
            "- Hijo dependiente dos",
            "",
            "Párrafo siguiente de texto plano que no termina en dos puntos.",
            "",
            "- Viñeta independiente uno",
            "- Viñeta independiente dos",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 6)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].level, 1)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].level, 1)
        self.assertEqual(blocks[3].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[3].level, 0)
        self.assertEqual(blocks[4].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[4].level, 0)
        self.assertEqual(blocks[5].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[5].level, 0)

    def test_fixture_b_nested_numbered_sub_list_hierarchy(self):
        lines: list[str] = [
            str(line) for line in FIXTURE_B_NESTED_NUMBERED_SUB_LIST.split("\n")[2:]
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=2)

        level_one_blocks = [b for b in blocks if b.level == 1]
        level_two_blocks = [b for b in blocks if b.level == 2]

        self.assertEqual(len(level_one_blocks), 8)
        self.assertEqual(len(level_two_blocks), 3)

    def test_opus_id_70_hierarchy_keeps_level_one_and_level_two_items_under_cap_eight(self):
        lines: list[str] = [
            str(line)
            for line in FIXTURE_M_OPUS_ID_70_PARAGRAPH_FLUSH_BULLETS_WITH_SUB_BULLETS.split("\n")[
                2:
            ]
        ]
        parser = FeedbackStructureParser(maximum_items_per_section=8)
        blocks = parser.parse(lines=lines, dimension_heading_level=2)

        level_zero_blocks = [b for b in blocks if b.level == 0]
        level_one_blocks = [b for b in blocks if b.level == 1]
        level_two_blocks = [b for b in blocks if b.level == 2]

        self.assertEqual(len(level_zero_blocks), 1)
        self.assertEqual(len(level_one_blocks), 6)
        self.assertEqual(len(level_two_blocks), 7)

    def test_opus_id_70_hierarchy_caps_level_one_children_when_cap_is_five(self):
        lines: list[str] = [
            str(line)
            for line in FIXTURE_M_OPUS_ID_70_PARAGRAPH_FLUSH_BULLETS_WITH_SUB_BULLETS.split("\n")[
                2:
            ]
        ]
        parser = FeedbackStructureParser(maximum_items_per_section=5)
        blocks = parser.parse(lines=lines, dimension_heading_level=2)

        level_zero_blocks = [b for b in blocks if b.level == 0]
        level_one_blocks = [b for b in blocks if b.level == 1]
        level_two_blocks = [b for b in blocks if b.level == 2]

        self.assertEqual(len(level_zero_blocks), 1)
        self.assertEqual(len(level_one_blocks), 5)
        self.assertEqual(len(level_two_blocks), 7)
        self.assertNotIn("Falta de contraste entre hipótesis", [b.text for b in blocks])

    def test_plain_line_ending_in_colon_without_preceding_blank_line_does_not_open_section_and_makes_items_children(
        self,
    ):
        lines = [
            "### Sección Principal",
            "Párrafo de texto explicativo.",
            "Por ejemplo:",
            "- Primer ejemplo ilustrativo",
            "- Segundo ejemplo ilustrativo",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 5)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Sección Principal")
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[1].text, "Párrafo de texto explicativo.")
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[2].text, "Por ejemplo:")
        self.assertEqual(blocks[2].level, 0)
        self.assertEqual(blocks[3].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[3].text, "Primer ejemplo ilustrativo")
        self.assertEqual(blocks[3].level, 1)
        self.assertEqual(blocks[4].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[4].text, "Segundo ejemplo ilustrativo")
        self.assertEqual(blocks[4].level, 1)
        self.assertNotIn(
            "Por ejemplo",
            [block.text for block in blocks if block.kind == FeedbackBlockKind.TITLE],
        )

    def test_plain_line_ending_in_colon_without_preceding_blank_line_does_not_reset_section_cap(
        self,
    ):
        lines = [
            "### Sección Principal",
            "- Elemento previo uno",
            "- Elemento previo dos",
            "Por ejemplo:",
            "- Primer ejemplo dependiente",
        ]
        parser = FeedbackStructureParser(maximum_items_per_section=2)
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[1].text, "Elemento previo uno")
        self.assertEqual(blocks[2].text, "Elemento previo dos")
        self.assertNotIn("Primer ejemplo dependiente", [block.text for block in blocks])

    def test_plain_line_ending_in_colon_preceded_by_blank_line_is_title(self):
        lines = [
            "### Sección Principal",
            "Párrafo de texto explicativo.",
            "",
            "Por ejemplo:",
            "- Primer ejemplo ilustrativo",
            "- Segundo ejemplo ilustrativo",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 5)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Sección Principal")
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[2].text, "Por ejemplo")
        self.assertEqual(blocks[3].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[3].text, "Primer ejemplo ilustrativo")
        self.assertEqual(blocks[3].level, 0)
        self.assertEqual(blocks[4].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[4].text, "Segundo ejemplo ilustrativo")
        self.assertEqual(blocks[4].level, 0)

    def test_first_non_empty_line_of_block_ending_in_colon_is_title(self):
        lines = [
            "",
            "Por ejemplo:",
            "- Primer ejemplo ilustrativo",
            "- Segundo ejemplo ilustrativo",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Por ejemplo")
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].text, "Primer ejemplo ilustrativo")
        self.assertEqual(blocks[1].level, 0)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].text, "Segundo ejemplo ilustrativo")
        self.assertEqual(blocks[2].level, 0)

    def test_plain_title_directly_under_heading_line_creates_title_and_drops_empty_heading(
        self,
    ) -> None:
        """A plain title directly below a heading opens a section and the empty heading is dropped."""
        lines = [
            "### Análisis",
            "Fortalezas:",
            "- Identificación clara del problema",
            "- Metodología robusta",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Fortalezas")
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].text, "Identificación clara del problema")
        self.assertEqual(blocks[1].level, 0)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].text, "Metodología robusta")
        self.assertEqual(blocks[2].level, 0)
        self.assertNotIn(
            "Análisis",
            [block.text for block in blocks],
        )

    def test_plain_title_directly_under_bold_only_line_creates_title_and_drops_empty_bold_heading(
        self,
    ) -> None:
        """A plain title directly below a bold-only line opens a section and empty heading is dropped."""
        lines = [
            "**Análisis General**",
            "Fortalezas:",
            "- Identificación clara del problema",
            "- Metodología robusta",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TITLE)
        self.assertEqual(blocks[0].text, "Fortalezas")
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].text, "Identificación clara del problema")
        self.assertEqual(blocks[1].level, 0)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].text, "Metodología robusta")
        self.assertEqual(blocks[2].level, 0)
        self.assertNotIn(
            "Análisis General",
            [block.text for block in blocks],
        )

    def test_plain_label_directly_under_table_row_is_not_title(self) -> None:
        """A plain label directly below a table row is parsed as text, not as a title."""
        lines = [
            "| Aspecto | Evaluación |",
            "|---|---|",
            "| Metodología | Adecuada |",
            "Observaciones:",
            "- Primera observación",
            "- Segunda observación",
        ]
        parser = FeedbackStructureParser()
        blocks = parser.parse(lines=lines, dimension_heading_level=0)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, FeedbackBlockKind.TEXT)
        self.assertEqual(blocks[0].text, "Observaciones:")
        self.assertEqual(blocks[0].level, 0)
        self.assertEqual(blocks[1].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[1].text, "Primera observación")
        self.assertEqual(blocks[1].level, 1)
        self.assertEqual(blocks[2].kind, FeedbackBlockKind.ITEM)
        self.assertEqual(blocks[2].text, "Segunda observación")
        self.assertEqual(blocks[2].level, 1)
        self.assertNotIn(
            "Observaciones",
            [block.text for block in blocks if block.kind == FeedbackBlockKind.TITLE],
        )

    def test_block_of_two_thousand_lines_accesses_lookahead_by_index_without_slicing_and_matches_small_version(
        self,
    ):
        class ObservedLineSequence(list):
            def __init__(self, elements=()):
                super().__init__(elements)
                self.slice_copied_count = 0
                self.index_read_count = 0

            def __getitem__(self, index_or_slice):
                if isinstance(index_or_slice, slice):
                    result = super().__getitem__(index_or_slice)
                    self.slice_copied_count += len(result)
                    return ObservedLineSequence(result)
                self.index_read_count += 1
                return super().__getitem__(index_or_slice)

        class ObservedFeedbackStructureParser(FeedbackStructureParser):
            def __init__(self) -> None:
                super().__init__()
                self.observed_prepared_lines = ObservedLineSequence()

            def _prepare_lines(self, lines: list[str]) -> list[tuple[str, int]]:
                prepared = super()._prepare_lines(lines)
                self.observed_prepared_lines = ObservedLineSequence(prepared)
                return self.observed_prepared_lines

        single_unit_lines = [
            "### Sección de prueba",
            "- Elemento de lista principal uno",
            "- Elemento de lista principal dos",
            "Párrafo explicativo que introduce detalles:",
            "- Sub-elemento dependiente alfa",
            "- Sub-elemento dependiente beta",
            "",
        ]
        parser = ObservedFeedbackStructureParser()
        single_unit_blocks = parser.parse(lines=single_unit_lines, dimension_heading_level=0)

        repeat_count = 350
        large_lines = single_unit_lines * repeat_count
        large_blocks = parser.parse(lines=large_lines, dimension_heading_level=0)

        self.assertEqual(parser.observed_prepared_lines.slice_copied_count, 0)
        self.assertLessEqual(
            parser.observed_prepared_lines.index_read_count,
            len(large_lines) * 2,
        )
        self.assertEqual(len(large_blocks), len(single_unit_blocks) * repeat_count)
        self.assertEqual(
            [block.text for block in large_blocks[: len(single_unit_blocks)]],
            [block.text for block in single_unit_blocks],
        )
