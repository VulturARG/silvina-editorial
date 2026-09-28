from json import loads
from os import path
from unittest import TestCase

from src.infrastructure.resources.laya import LAYA_RESOURCES_DIR


class TestLayaResources(TestCase):
    def test_laya_resources_directory_is_valid_directory(self):
        self.assertTrue(path.isdir(LAYA_RESOURCES_DIR))

    def test_decision_questions_file_exists(self):
        file_path = path.join(LAYA_RESOURCES_DIR, "decision_questions.json")
        self.assertTrue(path.isfile(file_path))

    def test_decision_questions_is_valid_json_with_nine_questions(self):
        questions = self._load_decision_questions()
        self.assertIsInstance(questions, list)
        self.assertEqual(len(questions), 9)

    def test_every_question_has_name_type_and_description(self):
        questions = self._load_decision_questions()
        for question in questions:
            self.assertIn("name", question)
            self.assertIn("type", question)
            self.assertIn("description", question)
            self.assertIsInstance(question["name"], str)
            self.assertIsInstance(question["type"], str)
            self.assertIsInstance(question["description"], str)
            self.assertTrue(len(question["name"]) > 0)
            self.assertTrue(len(question["type"]) > 0)
            self.assertTrue(len(question["description"]) > 0)

    def test_choice_questions_contain_valid_options_list(self):
        questions = self._load_decision_questions()
        choice_questions = [question for question in questions if question.get("type") == "choice"]
        self.assertEqual(len(choice_questions), 5)
        for question in choice_questions:
            self.assertIn("options", question)
            options = question["options"]
            self.assertIsInstance(options, list)
            self.assertTrue(len(options) > 0)
            for option in options:
                self.assertIsInstance(option, str)
                self.assertTrue(len(option) > 0)

    def test_score_questions_contain_min_and_max(self):
        questions = self._load_decision_questions()
        score_questions = [question for question in questions if question.get("type") == "score"]
        self.assertEqual(len(score_questions), 4)
        for question in score_questions:
            self.assertIn("min", question)
            self.assertIn("max", question)
            minimum_score = question["min"]
            maximum_score = question["max"]
            self.assertIsInstance(minimum_score, (int, float))
            self.assertIsInstance(maximum_score, (int, float))
            self.assertEqual(minimum_score, 0.0)
            self.assertEqual(maximum_score, 10.0)

    def test_decision_questions_contain_expected_names_in_order(self):
        questions = self._load_decision_questions()
        question_names = [question.get("name") for question in questions]
        expected_names = [
            "s4_intent",
            "s5_evidence",
            "s6_theory",
            "editorial_verdict",
            "research_line",
            "score_clarity",
            "score_coherence",
            "score_argumentation",
            "score_conclusions",
        ]
        self.assertEqual(question_names, expected_names)

    def test_specific_choice_questions_have_expected_options(self):
        questions = self._load_decision_questions()
        questions_by_name = {question["name"]: question for question in questions}

        self.assertEqual(questions_by_name["s4_intent"]["options"], ["SI", "NO"])
        self.assertEqual(questions_by_name["s5_evidence"]["options"], ["SI", "NO"])
        self.assertEqual(questions_by_name["s6_theory"]["options"], ["SI", "NO"])
        self.assertEqual(
            questions_by_name["editorial_verdict"]["options"],
            ["SUSTENTADA", "PARCIAL", "NO SUSTENTADA"],
        )
        self.assertEqual(
            questions_by_name["research_line"]["options"],
            ["1", "2", "3", "4", "5", "6", "7", "NINGUNA"],
        )

    def _load_decision_questions(self):
        file_path = path.join(LAYA_RESOURCES_DIR, "decision_questions.json")
        with open(file_path, "r", encoding="utf-8") as file_handle:
            return loads(file_handle.read())
