from unittest import TestCase

from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand
from src.infrastructure.wirings.document_analysis_command_wiring import (
    DocumentAnalysisCommandWiring,
)


class TestDocumentAnalysisCommandWiring(TestCase):
    def test_create_command_returns_document_analysis_command(self):
        command = DocumentAnalysisCommandWiring().create_command()

        self.assertIsInstance(command, DocumentAnalysisCommand)
