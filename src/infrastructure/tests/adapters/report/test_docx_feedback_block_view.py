from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.infrastructure.adapters.report.docx_feedback_block_payload import (
    DocxFeedbackBlockPayload,
)
from src.infrastructure.adapters.report.docx_feedback_block_view import DocxFeedbackBlockView


class TestDocxFeedbackBlockView(TestCase):
    def test_from_payload_resolves_title_kind(self) -> None:
        payload: DocxFeedbackBlockPayload = {
            "kind": "title",
            "text": "Fortalezas",
            "level": 0,
            "marker": "",
        }

        view = DocxFeedbackBlockView.from_payload(payload)

        self.assertEqual(view.kind, FeedbackBlockKind.TITLE)
        self.assertEqual(view.text, "Fortalezas")
        self.assertEqual(view.level, 0)
        self.assertEqual(view.marker, "")

    def test_from_payload_resolves_item_kind_with_level_and_marker(self) -> None:
        payload: DocxFeedbackBlockPayload = {
            "kind": "item",
            "text": "Aspecto positivo",
            "level": 1,
            "marker": "•",
        }

        view = DocxFeedbackBlockView.from_payload(payload)

        self.assertEqual(view.kind, FeedbackBlockKind.ITEM)
        self.assertEqual(view.text, "Aspecto positivo")
        self.assertEqual(view.level, 1)
        self.assertEqual(view.marker, "•")

    def test_from_payload_resolves_every_feedback_block_kind(self) -> None:
        for kind in FeedbackBlockKind:
            with self.subTest(kind=kind):
                view = DocxFeedbackBlockView.from_payload({"kind": kind.value})

                self.assertEqual(view.kind, kind)

    def test_from_payload_falls_back_to_text_kind_when_unknown(self) -> None:
        view = DocxFeedbackBlockView.from_payload({"kind": "custom_kind", "text": "Texto"})

        self.assertEqual(view.kind, FeedbackBlockKind.TEXT)
        self.assertEqual(view.text, "Texto")

    def test_from_payload_provides_defaults_when_fields_missing(self) -> None:
        view = DocxFeedbackBlockView.from_payload({"text": "Solo texto"})

        self.assertEqual(view.kind, FeedbackBlockKind.TEXT)
        self.assertEqual(view.text, "Solo texto")
        self.assertEqual(view.level, 0)
        self.assertEqual(view.marker, "")

    def test_from_payload_handles_empty_payload(self) -> None:
        view = DocxFeedbackBlockView.from_payload({})

        self.assertEqual(view.kind, FeedbackBlockKind.TEXT)
        self.assertEqual(view.text, "")
        self.assertEqual(view.level, 0)
        self.assertEqual(view.marker, "")

    def test_view_is_frozen_dataclass(self) -> None:
        view = DocxFeedbackBlockView(
            kind=FeedbackBlockKind.ITEM,
            text="Texto inmutable",
            level=0,
            marker="",
        )
        attribute_name = "text"

        with self.assertRaises(FrozenInstanceError):
            setattr(view, attribute_name, "Modificación no permitida")
