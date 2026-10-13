from contextlib import redirect_stdout
from io import StringIO
from logging import getLogger
from unittest import TestCase
from unittest.mock import Mock, patch

from main import main as run_main


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

    @patch("main.DocumentAnalysisCommandWiring")
    @patch("main.CommandLineArgumentParser")
    @patch("main.LoggingConfigWiring")
    def test_main_configures_logging_before_parsing_arguments_and_running_command(
        self,
        mock_logging_config_wiring_class,
        mock_argument_parser_class,
        mock_command_wiring_class,
    ) -> None:
        execution_order = []
        mock_logging_config_wiring_class.return_value.create_logging_config.return_value.configure.side_effect = (
            lambda: execution_order.append("configure_logging")
        )
        mock_argument_parser_class.return_value.parse.side_effect = lambda: (
            execution_order.append("parse_arguments") or Mock()
        )
        mock_command = mock_command_wiring_class.return_value.create_command.return_value
        mock_command.run.side_effect = lambda arguments: execution_order.append("run_command") or 0

        captured_output = StringIO()
        with redirect_stdout(captured_output):
            run_main()

        mock_logging_config_wiring_class.return_value.create_logging_config.return_value.configure.assert_called_once()
        self.assertEqual(
            execution_order,
            ["configure_logging", "parse_arguments", "run_command"],
        )

    @patch("main.DocumentAnalysisCommandWiring")
    @patch("main.CommandLineArgumentParser")
    @patch("main.LoggingConfigWiring")
    def test_main_ordering_with_mock_parent(
        self,
        mock_logging_config_wiring_class,
        mock_argument_parser_class,
        mock_command_wiring_class,
    ) -> None:
        manager = Mock()
        manager.attach_mock(mock_logging_config_wiring_class, "LoggingConfigWiring")
        manager.attach_mock(mock_argument_parser_class, "CommandLineArgumentParser")
        manager.attach_mock(mock_command_wiring_class, "DocumentAnalysisCommandWiring")
        mock_command_wiring_class.return_value.create_command.return_value.run.return_value = 0

        captured_output = StringIO()
        with redirect_stdout(captured_output):
            run_main()

        call_names = [call[0] for call in manager.mock_calls]
        configure_index = call_names.index(
            "LoggingConfigWiring().create_logging_config().configure"
        )
        parse_index = call_names.index("CommandLineArgumentParser().parse")
        run_index = call_names.index("DocumentAnalysisCommandWiring().create_command().run")
        self.assertLess(configure_index, parse_index)
        self.assertLess(parse_index, run_index)
