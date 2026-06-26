from dataclasses import FrozenInstanceError
from inspect import getsource, signature
from sys import modules
from unittest import TestCase

from src.domain.document.character_count_port import CharacterCountPort
from src.domain.dtos.character_count_dto import CharacterCountDTO


class TestCharacterCountPort(TestCase):
    def test_is_abstract_base_class(self):
        with self.assertRaises(TypeError):
            CharacterCountPort()

    def test_declares_exactly_one_abstract_method_count(self):
        self.assertEqual(CharacterCountPort.__abstractmethods__, frozenset({"count"}))

    def test_count_signature_has_docx_path_parameter(self):
        sig = signature(CharacterCountPort.count)
        self.assertIn("docx_path", sig.parameters)

    def test_module_has_no_win32com_imports(self):
        module_source = getsource(modules[CharacterCountPort.__module__])
        self.assertNotIn("win32com", module_source)
        self.assertNotIn("src.infrastructure", module_source)

    def test_character_count_dto_raises_frozen_instance_error_on_reassignment(self):
        dto = CharacterCountDTO(word_count=100, char_count=500, paragraph_count=10)
        with self.assertRaises(FrozenInstanceError):
            dto.word_count = 0
