from os import environ
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.ensure_language_model_server_use_case import (
    EnsureLanguageModelServerUseCase,
)
from src.application.export_report_use_case import ExportReportUseCase
from src.application.release_language_model_server_use_case import (
    ReleaseLanguageModelServerUseCase,
)
from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter import (
    OllamaLanguageModelWarmupAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_server_adapter import (
    OllamaServerAdapter,
)
from src.infrastructure.cli.cli_analysis_services import CliAnalysisServices
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.wirings.cli_analysis_services_wiring import (
    CliAnalysisServicesWiring,
)
from src.infrastructure.wirings.overridable_warm_up_language_model_use_case_wiring import (
    OverridableWarmUpLanguageModelUseCaseWiring,
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

    def test_warm_up_use_case_is_warm_up_language_model_use_case(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertIsInstance(services.warm_up_language_model_use_case, WarmUpLanguageModelUseCase)

    def test_ensure_language_model_server_use_case_is_ensure_language_model_server_use_case(
        self,
    ):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertIsInstance(
            services.ensure_language_model_server_use_case,
            EnsureLanguageModelServerUseCase,
        )

    def test_ensure_language_model_server_use_case_receives_environment_overrides(self):
        overrides = {"OLLAMA_BASE_URL": "http://127.0.0.1:11439"}
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring(overrides).create_services()

        server_port = services.ensure_language_model_server_use_case._language_model_server_starter._language_model_server_port
        self.assertIsInstance(server_port, OllamaServerAdapter)
        assert isinstance(server_port, OllamaServerAdapter)
        self.assertEqual(server_port._base_url, "http://127.0.0.1:11439")

    def test_warm_up_use_case_receives_environment_overrides(self):
        overrides = {"OLLAMA_MODEL_NAME": "override-model"}
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring(overrides).create_services()

        warmer_port = services.warm_up_language_model_use_case._language_model_warmer._language_model_warmup_port
        self.assertIsInstance(warmer_port, OllamaLanguageModelWarmupAdapter)
        assert isinstance(warmer_port, OllamaLanguageModelWarmupAdapter)
        self.assertEqual(warmer_port._model_name, "override-model")

    def test_does_not_use_base_warm_up_language_model_use_case_wiring_without_overrides(
        self,
    ):
        overrides = {"OLLAMA_MODEL_NAME": "override-model"}
        with (
            patch.dict(environ, self._complete_environment(), clear=True),
            patch(
                "src.infrastructure.wirings.cli_analysis_services_wiring.OverridableWarmUpLanguageModelUseCaseWiring",
                autospec=OverridableWarmUpLanguageModelUseCaseWiring,
            ) as mock_overridable_wiring,
        ):
            mock_overridable_wiring.return_value.get_warm_up_language_model_use_case.return_value = MagicMock(
                spec=WarmUpLanguageModelUseCase
            )
            CliAnalysisServicesWiring(overrides).create_services()

        mock_overridable_wiring.assert_called_once_with(overrides)

    def test_passes_prompt_file_overrides_to_analyze_document_use_case_wiring(self):
        prompt_file_overrides = {
            "s4_s5_s6_signal_prompt": Path("custom/s4_s5_s6_signal_prompt.txt")
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = CliAnalysisServicesWiring({}, prompt_file_overrides=prompt_file_overrides)
            analyze_wiring = wiring._analyze_document_use_case_wiring()

        self.assertEqual(analyze_wiring._prompt_file_overrides, prompt_file_overrides)

    def test_release_language_model_server_use_case_is_release_language_model_server_use_case(
        self,
    ):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertIsInstance(
            services.release_language_model_server_use_case,
            ReleaseLanguageModelServerUseCase,
        )

    def test_release_language_model_server_use_case_receives_environment_overrides(self):
        overrides = {"OLLAMA_BASE_URL": "http://127.0.0.1:11439"}
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring(overrides).create_services()

        server_port = services.release_language_model_server_use_case._language_model_server_starter._language_model_server_port
        self.assertIsInstance(server_port, OllamaServerAdapter)
        assert isinstance(server_port, OllamaServerAdapter)
        self.assertEqual(server_port._base_url, "http://127.0.0.1:11439")

    def test_services_uses_local_language_model_is_true_by_default_for_ollama(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertTrue(services.uses_local_language_model)
        self.assertTrue(services.warms_up_language_model)

    def test_services_uses_local_language_model_is_false_for_external_provider(self):
        overrides = {
            "APP_MODE": "DEBUG",
            "USE_EXTERNAL_LLM": "true",
            "LLM_PROVIDER": "claude",
            "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring(overrides).create_services()

        self.assertFalse(services.uses_local_language_model)
        self.assertFalse(services.warms_up_language_model)

    def test_services_warms_up_language_model_is_false_when_startup_warmup_disabled(self):
        overrides = {"OLLAMA_WARMUP_ON_STARTUP": "false"}
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring(overrides).create_services()

        self.assertTrue(services.uses_local_language_model)
        self.assertFalse(services.warms_up_language_model)
