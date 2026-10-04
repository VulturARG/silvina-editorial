from unittest import TestCase

from src.domain.dtos.feedback_line_dto import FeedbackLineDTO


class TestFeedbackLineDTO(TestCase):
    def test_creates_dto_with_text_and_indentation(self):
        dto = FeedbackLineDTO(text="Sample line", indentation=4)

        self.assertEqual(dto.text, "Sample line")
        self.assertEqual(dto.indentation, 4)

    def test_as_dict_returns_dictionary_representation(self):
        dto = FeedbackLineDTO(text="Indented text", indentation=2)

        self.assertEqual(
            dto.as_dict(),
            {"text": "Indented text", "indentation": 2},
        )

    def test_from_dict_creates_instance(self):
        dto = FeedbackLineDTO.from_dict({"text": "From dict text", "indentation": 0})

        self.assertEqual(dto.text, "From dict text")
        self.assertEqual(dto.indentation, 0)
