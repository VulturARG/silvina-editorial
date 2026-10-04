from unittest import TestCase

from src.domain.dtos.feedback_line_dto import FeedbackLineDTO
from src.domain.enums.feedback_line_kind import FeedbackLineKind
from src.domain.quality.feedback_line_classifier import FeedbackLineClassifier
from src.domain.quality.feedback_list_marker import FeedbackListMarker


class TestFeedbackLineClassifier(TestCase):
    def test_prepare_lines_removes_blockquotes_and_calculates_indentation(self):
        classifier = FeedbackLineClassifier()
        raw_lines = [
            "> ### Encabezado",
            "  - Elemento sangrado",
            ">   Texto con sangría tras cita",
            "",
            "   ",
        ]

        prepared = classifier.prepare_lines(raw_lines)

        self.assertEqual(len(prepared), 5)
        self.assertEqual(prepared[0], FeedbackLineDTO(text="### Encabezado", indentation=0))
        self.assertEqual(prepared[1], FeedbackLineDTO(text="- Elemento sangrado", indentation=2))
        self.assertEqual(
            prepared[2], FeedbackLineDTO(text="Texto con sangría tras cita", indentation=0)
        )
        self.assertEqual(prepared[3], FeedbackLineDTO(text="", indentation=0))
        self.assertEqual(prepared[4], FeedbackLineDTO(text="", indentation=0))

    def test_find_next_non_empty_line_finds_first_following_content_line(self):
        classifier = FeedbackLineClassifier()
        lines = [
            FeedbackLineDTO(text="Inicio", indentation=0),
            FeedbackLineDTO(text="", indentation=0),
            FeedbackLineDTO(text="Siguiente contenido", indentation=2),
        ]

        found = classifier.find_next_non_empty_line(lines, current_index=0)

        self.assertEqual(found, FeedbackLineDTO(text="Siguiente contenido", indentation=2))
        self.assertIsNone(classifier.find_next_non_empty_line(lines, current_index=2))

    def test_classifies_horizontal_rules(self):
        classifier = FeedbackLineClassifier()

        for rule in ("---", "- - -", "***", "* * *", "___"):
            line = FeedbackLineDTO(text=rule, indentation=0)
            classified = classifier.classify(line)
            self.assertEqual(classified.kind, FeedbackLineKind.HORIZONTAL_RULE)

    def test_classifies_table_row(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="| Celda 1 | Celda 2 |", indentation=0)
        classified = classifier.classify(line)

        self.assertEqual(classified.kind, FeedbackLineKind.TABLE_ROW)

    def test_classifies_heading_and_extracts_level_and_title(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="### **Fortalezas observadas:**", indentation=0)
        classified = classifier.classify(line)

        self.assertEqual(classified.kind, FeedbackLineKind.HEADING)
        self.assertEqual(classified.heading_level, 3)
        self.assertEqual(classified.title_text, "**Fortalezas observadas:**")

    def test_classifies_bold_title(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="**Aspectos a mejorar:**", indentation=0)
        classified = classifier.classify(line)

        self.assertEqual(classified.kind, FeedbackLineKind.BOLD_TITLE)
        self.assertEqual(classified.title_text, "**Aspectos a mejorar:**")

    def test_classifies_plain_title_when_all_guards_pass(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="Puntos críticos observados:", indentation=0)
        next_line = FeedbackLineDTO(text="- Primer punto", indentation=0)

        classified = classifier.classify(
            line=line,
            next_line=next_line,
            is_preceded_by_blank=True,
        )

        self.assertEqual(classified.kind, FeedbackLineKind.PLAIN_TITLE)
        self.assertEqual(classified.title_text, "Puntos críticos observados:")

    def test_plain_title_candidate_rejected_when_not_preceded_by_blank(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="Puntos críticos observados:", indentation=0)
        next_line = FeedbackLineDTO(text="- Primer punto", indentation=0)

        classified = classifier.classify(
            line=line,
            next_line=next_line,
            is_preceded_by_blank=False,
        )

        self.assertEqual(classified.kind, FeedbackLineKind.TEXT)

    def test_plain_title_candidate_rejected_when_sentence_terminal_punctuation_inside(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="Punto uno. Punto dos:", indentation=0)
        next_line = FeedbackLineDTO(text="- Primer punto", indentation=0)

        classified = classifier.classify(
            line=line,
            next_line=next_line,
            is_preceded_by_blank=True,
        )

        self.assertEqual(classified.kind, FeedbackLineKind.TEXT)

    def test_plain_title_candidate_rejected_when_starts_with_bold(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="**Punto no calificado:", indentation=0)
        next_line = FeedbackLineDTO(text="- Primer punto", indentation=0)

        classified = classifier.classify(
            line=line,
            next_line=next_line,
            is_preceded_by_blank=True,
        )

        self.assertEqual(classified.kind, FeedbackLineKind.TEXT)

    def test_plain_title_candidate_rejected_when_not_followed_by_list(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="Puntos críticos observados:", indentation=0)
        next_line = FeedbackLineDTO(text="Párrafo normal siguiente", indentation=0)

        classified = classifier.classify(
            line=line,
            next_line=next_line,
            is_preceded_by_blank=True,
        )

        self.assertEqual(classified.kind, FeedbackLineKind.TEXT)

    def test_classifies_bullets_and_extracts_marker_and_content(self):
        classifier = FeedbackLineClassifier()
        for bullet_text in ("- Guión", "* Asterisco", "+ Más"):
            line = FeedbackLineDTO(text=bullet_text, indentation=0)
            classified = classifier.classify(line)
            self.assertEqual(classified.kind, FeedbackLineKind.BULLET)
            self.assertEqual(classified.list_marker, FeedbackListMarker.BULLET)

        line = FeedbackLineDTO(text="- Contenido de prueba", indentation=0)
        classified = classifier.classify(line)
        self.assertEqual(classified.item_content, "Contenido de prueba")

    def test_classifies_numbered_items_and_extracts_marker_and_content(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="12. Elemento duodécimo", indentation=0)
        classified = classifier.classify(line)

        self.assertEqual(classified.kind, FeedbackLineKind.NUMBERED)
        self.assertEqual(classified.list_marker, "12.")
        self.assertEqual(classified.item_content, "Elemento duodécimo")

    def test_starts_unindented_children_set_on_text_ending_in_colon_followed_by_list(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="Detalles observados:", indentation=0)
        next_line = FeedbackLineDTO(text="- Primer punto", indentation=0)
        classified = classifier.classify(line, next_line=next_line)

        self.assertTrue(classified.starts_unindented_children)

    def test_starts_unindented_children_false_when_not_ending_in_colon(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="Detalles observados", indentation=0)
        next_line = FeedbackLineDTO(text="- Primer punto", indentation=0)
        classified = classifier.classify(line, next_line=next_line)

        self.assertFalse(classified.starts_unindented_children)

    def test_starts_unindented_children_false_when_next_line_is_none_or_not_list(self):
        classifier = FeedbackLineClassifier()
        line = FeedbackLineDTO(text="Detalles observados:", indentation=0)
        non_list_next = FeedbackLineDTO(text="Texto plano", indentation=0)

        self.assertFalse(classifier.classify(line, next_line=None).starts_unindented_children)
        self.assertFalse(
            classifier.classify(line, next_line=non_list_next).starts_unindented_children
        )

    def test_starts_unindented_children_for_list_item_compares_indentation(self):
        classifier = FeedbackLineClassifier()
        list_line = FeedbackLineDTO(text="- Elemento con detalle:", indentation=2)
        deeper_child = FeedbackLineDTO(text="- Sub-elemento", indentation=4)
        flush_child = FeedbackLineDTO(text="- Sub-elemento al mismo nivel", indentation=2)

        self.assertFalse(
            classifier.classify(list_line, next_line=deeper_child).starts_unindented_children
        )
        self.assertTrue(
            classifier.classify(list_line, next_line=flush_child).starts_unindented_children
        )
