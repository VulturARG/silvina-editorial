from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import TestCase

from src.infrastructure.cli.batch_command_line_argument_parser import (
    BatchCommandLineArgumentParser,
)


class TestBatchCommandLineArgumentParser(TestCase):
    def setUp(self):
        self.parser = BatchCommandLineArgumentParser()

    def test_parses_batch_file_positional_as_path(self):
        batch_file_path = self.parser.parse(["batches/main.toml"])

        self.assertEqual(batch_file_path, Path("batches/main.toml"))

    def test_rejects_missing_batch_file_with_usage_error(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as context:
            self.parser.parse([])

        self.assertEqual(context.exception.code, 2)
