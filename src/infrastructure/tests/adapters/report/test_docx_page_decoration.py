from abc import ABC
from unittest import TestCase

from src.infrastructure.adapters.report.docx_page_decoration import DocxPageDecoration


class TestDocxPageDecoration(TestCase):
    def test_is_abstract_base_class(self) -> None:
        self.assertTrue(issubclass(DocxPageDecoration, ABC))

    def test_declares_apply_as_its_only_abstract_method(self) -> None:
        self.assertEqual(DocxPageDecoration.__abstractmethods__, frozenset({"apply"}))
