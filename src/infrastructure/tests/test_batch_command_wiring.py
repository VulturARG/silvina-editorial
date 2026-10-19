from unittest import TestCase

from src.infrastructure.cli.batch_command import BatchCommand
from src.infrastructure.wirings.batch_command_wiring import BatchCommandWiring


class TestBatchCommandWiring(TestCase):
    def test_create_command_returns_batch_command(self):
        command = BatchCommandWiring().create_command()

        self.assertIsInstance(command, BatchCommand)
