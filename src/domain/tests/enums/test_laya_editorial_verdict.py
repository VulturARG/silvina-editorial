from unittest import TestCase

from src.domain.enums.laya_editorial_verdict import LayaEditorialVerdict


class TestLayaEditorialVerdict(TestCase):
    def test_members_match_laya_question_criteria_labels(self):
        self.assertEqual(LayaEditorialVerdict.SUSTAINED.value, "SUSTENTADA")
        self.assertEqual(LayaEditorialVerdict.PARTIAL.value, "PARCIAL")
        self.assertEqual(LayaEditorialVerdict.NOT_SUSTAINED.value, "NO SUSTENTADA")

    def test_member_count(self):
        self.assertEqual(len(LayaEditorialVerdict), 3)
