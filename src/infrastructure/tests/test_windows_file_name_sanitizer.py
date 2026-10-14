from unittest import TestCase

from src.infrastructure.cli.windows_file_name_sanitizer import WindowsFileNameSanitizer


class TestWindowsFileNameSanitizer(TestCase):
    INVALID_CHARACTERS = '<>:"/\\|?*'

    def setUp(self):
        self.sanitizer = WindowsFileNameSanitizer()

    def test_replaces_each_invalid_character_with_underscore(self):
        for invalid_character in self.INVALID_CHARACTERS:
            with self.subTest(invalid_character=invalid_character):
                self.assertEqual(self.sanitizer.sanitize(f"a{invalid_character}b"), "a_b")

    def test_replaces_every_invalid_character_in_the_same_text(self):
        self.assertEqual(self.sanitizer.sanitize('a<b>c:d"e/f\\g|h?i*j'), "a_b_c_d_e_f_g_h_i_j")

    def test_keeps_accents_spaces_dots_hyphens_and_parentheses(self):
        text = "Tesis Año 2026-final.v2 (copia)"

        self.assertEqual(self.sanitizer.sanitize(text), text)

    def test_returns_empty_text_unchanged(self):
        self.assertEqual(self.sanitizer.sanitize(""), "")
