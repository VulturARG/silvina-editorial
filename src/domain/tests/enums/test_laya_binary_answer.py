from unittest import TestCase

from src.domain.enums.laya_binary_answer import LayaBinaryAnswer


class TestLayaBinaryAnswer(TestCase):
    def test_members_match_laya_question_criteria_labels(self):
        self.assertEqual(LayaBinaryAnswer.YES.value, "SI")
        self.assertEqual(LayaBinaryAnswer.NO.value, "NO")

    def test_member_count(self):
        self.assertEqual(len(LayaBinaryAnswer), 2)
