from unittest import TestCase

from src.domain.enums.laya_research_line_answer import LayaResearchLineAnswer


class TestLayaResearchLineAnswer(TestCase):
    def test_none_member_matches_laya_question_criteria_label(self):
        self.assertEqual(LayaResearchLineAnswer.NONE.value, "NINGUNA")
