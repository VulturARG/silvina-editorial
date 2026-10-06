from contextlib import redirect_stdout
from io import StringIO
from logging import getLogger
from unittest import TestCase
from unittest.mock import Mock, patch

import main


class TestMainLogging(TestCase):
    """Test suite verifying logging initialization in main CLI entry point."""

    def setUp(self) -> None:
        self._root_logger = getLogger()
        self._initial_root_handlers = list(self._root_logger.handlers)
        self._initial_root_level = self._root_logger.level

    def tearDown(self) -> None:
        for handler in list(self._root_logger.handlers):
            if handler not in self._initial_root_handlers:
                self._root_logger.removeHandler(handler)
                handler.close()
        for handler in self._initial_root_handlers:
            if handler not in self._root_logger.handlers:
                self._root_logger.addHandler(handler)
        self._root_logger.setLevel(self._initial_root_level)

    @patch("main.SilvinaEditorialAssistant")
    @patch("main.exists", return_value=True)
    @patch("main._build_argument_parser")
    @patch("main.LoggingConfigWiring")
    def test_main_configures_logging_before_other_collaborators(
        self,
        mock_logging_config_wiring_class,
        mock_build_argument_parser,
        mock_exists,
        mock_assistant_class,
    ) -> None:
        execution_order = []
        mock_logging_config_wiring_class.return_value.create_logging_config.return_value.configure.side_effect = (
            lambda: execution_order.append("configure_logging")
        )

        mock_arguments = Mock()
        mock_arguments.document_path = "document.docx"
        mock_arguments.output_dir = None
        mock_arguments.word_report_path = None
        mock_arguments.json_report_path = None

        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_arguments
        mock_build_argument_parser.side_effect = lambda: (
            execution_order.append("build_argument_parser") or mock_parser
        )

        mock_assistant = mock_assistant_class.return_value
        mock_assistant.analyze_document.return_value = {
            "document_info": {"word_count": 100, "char_count": 500},
            "classification": {
                "category": Mock(value="scientific"),
                "article_size": Mock(value="short"),
                "reasoning": "reasoning",
            },
            "quality_analysis": {
                "overall_score": 8.0,
                "gramatica": {"score": 8.0, "feedback": "good", "errors": []},
                "dimensions": {},
            },
            "structure_validation": {"is_valid": True, "missing_sections": []},
            "citations_analysis": {"total_citations": 0},
            "recommendations": [],
        }
        mock_assistant.save_word_report.return_value = True
        mock_assistant_class.side_effect = lambda: (
            execution_order.append("assistant_init") or mock_assistant
        )

        captured_output = StringIO()
        with redirect_stdout(captured_output):
            main.main()

        mock_logging_config_wiring_class.return_value.create_logging_config.return_value.configure.assert_called_once()
        self.assertEqual(
            execution_order,
            ["configure_logging", "build_argument_parser", "assistant_init"],
        )

    @patch("main.SilvinaEditorialAssistant")
    @patch("main.exists", return_value=True)
    @patch("main._build_argument_parser")
    @patch("main.LoggingConfigWiring")
    def test_main_ordering_with_mock_parent(
        self,
        mock_logging_config_wiring_class,
        mock_build_argument_parser,
        mock_exists,
        mock_assistant_class,
    ) -> None:
        manager = Mock()
        manager.attach_mock(mock_logging_config_wiring_class, "LoggingConfigWiring")
        manager.attach_mock(mock_build_argument_parser, "_build_argument_parser")
        manager.attach_mock(mock_assistant_class, "SilvinaEditorialAssistant")

        mock_arguments = Mock()
        mock_arguments.document_path = "document.docx"
        mock_arguments.output_dir = None
        mock_arguments.word_report_path = None
        mock_arguments.json_report_path = None

        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_arguments
        mock_build_argument_parser.return_value = mock_parser

        mock_assistant = mock_assistant_class.return_value
        mock_assistant.analyze_document.return_value = {
            "document_info": {"word_count": 100, "char_count": 500},
            "classification": {
                "category": Mock(value="scientific"),
                "article_size": Mock(value="short"),
                "reasoning": "reasoning",
            },
            "quality_analysis": {
                "overall_score": 8.0,
                "gramatica": {"score": 8.0, "feedback": "good", "errors": []},
                "dimensions": {},
            },
            "structure_validation": {"is_valid": True, "missing_sections": []},
            "citations_analysis": {"total_citations": 0},
            "recommendations": [],
        }
        mock_assistant.save_word_report.return_value = True

        captured_output = StringIO()
        with redirect_stdout(captured_output):
            main.main()

        call_names = [call[0] for call in manager.mock_calls]
        configure_index = call_names.index(
            "LoggingConfigWiring().create_logging_config().configure"
        )
        build_parser_index = call_names.index("_build_argument_parser")
        assistant_index = call_names.index("SilvinaEditorialAssistant")
        self.assertLess(configure_index, build_parser_index)
        self.assertLess(build_parser_index, assistant_index)
