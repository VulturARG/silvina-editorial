from unittest import TestCase

from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.quality.feedback_structure_parser import FeedbackStructureParser


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
