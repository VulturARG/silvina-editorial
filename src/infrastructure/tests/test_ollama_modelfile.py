from os.path import join
from pathlib import Path
from unittest import TestCase

from src.infrastructure.resources.ollama import MODELFILE_DIR
from src.infrastructure.resources.text_resource_loader import read_text_resource


class TestOllamaModelfile(TestCase):
    MODELFILE_FILENAME = "gemma4-26b-adapted.Modelfile"

    def test_first_non_empty_line_specifies_expected_base_model(self):
        content = read_text_resource(directory=MODELFILE_DIR, filename=self.MODELFILE_FILENAME)
        non_empty_lines = [line for line in content.splitlines() if line.strip()]
        self.assertEqual(
            non_empty_lines[0],
            "FROM hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS",
        )

    def test_declares_gemma4_renderer(self):
        content = read_text_resource(directory=MODELFILE_DIR, filename=self.MODELFILE_FILENAME)
        self.assertIn("RENDERER gemma4", content.splitlines())

    def test_declares_gemma4_parser(self):
        content = read_text_resource(directory=MODELFILE_DIR, filename=self.MODELFILE_FILENAME)
        self.assertIn("PARSER gemma4", content.splitlines())

    def test_template_closes_thought_channel(self):
        content = read_text_resource(directory=MODELFILE_DIR, filename=self.MODELFILE_FILENAME)
        self.assertIn(
            "<|channel>thought\n<channel|>{{ .Response }}<turn|>",
            content,
        )

    def test_declares_stop_parameters(self):
        content = read_text_resource(directory=MODELFILE_DIR, filename=self.MODELFILE_FILENAME)
        lines = content.splitlines()
        self.assertIn("PARAMETER stop <turn|>", lines)
        self.assertIn("PARAMETER stop <|turn>", lines)

    def test_contains_no_carriage_return_bytes(self):
        modelfile_bytes = Path(join(MODELFILE_DIR, self.MODELFILE_FILENAME)).read_bytes()
        self.assertNotIn(b"\r", modelfile_bytes)
