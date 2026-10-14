from os import environ
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.export_report_use_case import ExportReportUseCase
from src.infrastructure.cli.cli_analysis_services import CliAnalysisServices
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.wirings.cli_analysis_services_wiring import (
    CliAnalysisServicesWiring,
)
from src.infrastructure.wirings.warm_up_language_model_use_case_wiring import (
    WarmUpLanguageModelUseCaseWiring,
)


class TestCliAnalysisServicesWiring(TestCase):
    ENVIRONMENT_MODEL_NAME = "gemma4-26b-adapted"

    @staticmethod
    def _complete_environment() -> dict[str, str]:
        return {
            **CompleteTestEnvironment.application_variables(),
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }

    def test_create_services_returns_cli_analysis_services(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertIsInstance(services, CliAnalysisServices)

    def test_analysis_use_case_is_analyze_document_use_case(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertIsInstance(services.analyze_document_use_case, AnalyzeDocumentUseCase)

    def test_report_use_cases_are_export_report_use_cases(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertIsInstance(services.word_report_use_case, ExportReportUseCase)
        self.assertIsInstance(services.json_report_use_case, ExportReportUseCase)
        self.assertIsInstance(services.html_report_use_case, ExportReportUseCase)

    def test_model_name_follows_ollama_model_name_override(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring(
                {"OLLAMA_MODEL_NAME": "override-model"}
            ).create_services()

        self.assertEqual(services.model_name, "override-model")

    def test_model_name_comes_from_environment_without_overrides(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertEqual(services.model_name, self.ENVIRONMENT_MODEL_NAME)

    def test_environment_is_not_modified_after_creating_services(self):
        overrides = {"OLLAMA_MODEL_NAME": "override-model", "LLM_PROVIDER": "claude"}
        with patch.dict(environ, self._complete_environment(), clear=True):
            environment_before = dict(environ)
            CliAnalysisServicesWiring(overrides).create_services()
            environment_after = dict(environ)

        self.assertEqual(environment_after, environment_before)
        self.assertNotIn("LLM_PROVIDER", environment_after)

    def test_does_not_use_warm_up_language_model_use_case_wiring(self):
        with (
            patch.dict(environ, self._complete_environment(), clear=True),
            patch.object(
                WarmUpLanguageModelUseCaseWiring, "get_warm_up_language_model_use_case"
            ) as warm_up_factory,
        ):
            CliAnalysisServicesWiring({}).create_services()

        warm_up_factory.assert_not_called()

    def test_passes_prompt_file_overrides_to_analyze_document_use_case_wiring(self):
        prompt_file_overrides = {
            "s4_s5_s6_signal_prompt": Path("custom/s4_s5_s6_signal_prompt.txt")
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = CliAnalysisServicesWiring({}, prompt_file_overrides=prompt_file_overrides)
            analyze_wiring = wiring._analyze_document_use_case_wiring()

        self.assertEqual(analyze_wiring._prompt_file_overrides, prompt_file_overrides)
