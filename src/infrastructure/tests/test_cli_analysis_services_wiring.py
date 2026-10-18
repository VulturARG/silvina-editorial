from json import load
from os import environ
from os.path import join
from pathlib import Path
from shutil import copytree, ignore_patterns
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch

from docx import Document

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.ensure_language_model_server_use_case import (
    EnsureLanguageModelServerUseCase,
)
from src.application.export_report_use_case import ExportReportUseCase
from src.application.release_language_model_server_use_case import (
    ReleaseLanguageModelServerUseCase,
)
from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.adapters.llm_generator.ollama_language_model_warmup_adapter import (
    OllamaLanguageModelWarmupAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_server_adapter import (
    OllamaServerAdapter,
)
from src.infrastructure.cli.cli_analysis_services import CliAnalysisServices
from src.infrastructure.resources.prompts import PROMPTS_ROOT
from src.infrastructure.tests.adapters.report.characterization_report_input import (
    CharacterizationReportInput,
)
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
    REPLACED_PROMPTS_DESCRIPTION = "default + alignment_prompt, research_lines"

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

    def test_passes_prompts_root_to_analyze_document_use_case_wiring(self):
        prompts_root = Path("custom/prompts")
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = CliAnalysisServicesWiring({}, prompts_root=prompts_root)
            analyze_wiring = wiring._analyze_document_use_case_wiring()

        self.assertEqual(
            analyze_wiring._classification_prompts_directory,
            str(prompts_root / "classification"),
        )
        self.assertEqual(
            analyze_wiring._quality_prompts_directory,
            str(prompts_root / "quality"),
        )

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

    def test_prompt_source_is_default_without_custom_prompts(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring({}).create_services()

        self.assertEqual(
            services.prompt_source,
            PromptSourceDTO(base_label="default", replaced_prompt_names=()),
        )

    def test_prompt_source_names_root_folder_when_prompts_root_is_given(self):
        with TemporaryDirectory() as temporary_directory:
            prompts_root = self._copy_packaged_prompts_root(Path(temporary_directory) / "v2")
            with patch.dict(environ, self._complete_environment(), clear=True):
                services = CliAnalysisServicesWiring(
                    {}, prompts_root=prompts_root
                ).create_services()

        self.assertEqual(services.prompt_source.describe(), "v2")

    def test_prompt_source_lists_replaced_prompts_in_fixed_order(self):
        prompt_file_overrides = {
            "research_lines": PROMPTS_ROOT / "quality" / "research_lines.txt",
            "alignment_prompt": PROMPTS_ROOT / "quality" / "alignment_prompt.txt",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring(
                {}, prompt_file_overrides=prompt_file_overrides
            ).create_services()

        self.assertEqual(
            services.prompt_source,
            PromptSourceDTO(
                base_label="default",
                replaced_prompt_names=("alignment_prompt", "research_lines"),
            ),
        )

    def test_prompt_source_combines_root_folder_and_replaced_prompts(self):
        with TemporaryDirectory() as temporary_directory:
            prompts_root = self._copy_packaged_prompts_root(Path(temporary_directory) / "v2")
            prompt_file_overrides = {
                "research_lines": prompts_root / "quality" / "research_lines.txt",
                "alignment_prompt": prompts_root / "quality" / "alignment_prompt.txt",
            }
            with patch.dict(environ, self._complete_environment(), clear=True):
                services = CliAnalysisServicesWiring(
                    {},
                    prompt_file_overrides=prompt_file_overrides,
                    prompts_root=prompts_root,
                ).create_services()

        self.assertEqual(
            services.prompt_source.describe(),
            "v2 + alignment_prompt, research_lines",
        )

    def test_word_report_use_case_shows_the_run_prompt_source(self):
        services = self._services_with_replaced_prompts()
        with TemporaryDirectory() as temporary_directory:
            output_path = join(temporary_directory, "report.docx")
            services.word_report_use_case.execute(
                report_input=CharacterizationReportInput.build(), output_path=output_path
            )
            paragraph_texts = [paragraph.text for paragraph in Document(output_path).paragraphs]

        self.assertIn(f"Prompts utilizados: {self.REPLACED_PROMPTS_DESCRIPTION}", paragraph_texts)

    def test_json_report_use_case_writes_the_run_prompt_source(self):
        services = self._services_with_replaced_prompts()
        with TemporaryDirectory() as temporary_directory:
            output_path = join(temporary_directory, "report.json")
            services.json_report_use_case.execute(
                report_input=CharacterizationReportInput.build(), output_path=output_path
            )
            with open(output_path, encoding="utf-8") as file:
                written_data = load(file)

        self.assertEqual(written_data["prompt_source"], self.REPLACED_PROMPTS_DESCRIPTION)

    def test_html_report_use_case_shows_the_run_prompt_source(self):
        services = self._services_with_replaced_prompts()
        with TemporaryDirectory() as temporary_directory:
            output_path = join(temporary_directory, "report.html")
            services.html_report_use_case.execute(
                report_input=CharacterizationReportInput.build(), output_path=output_path
            )
            with open(output_path, encoding="utf-8") as file:
                html = file.read()

        self.assertIn(self.REPLACED_PROMPTS_DESCRIPTION, html)

    def _services_with_replaced_prompts(self) -> CliAnalysisServices:
        prompt_file_overrides = {
            "research_lines": PROMPTS_ROOT / "quality" / "research_lines.txt",
            "alignment_prompt": PROMPTS_ROOT / "quality" / "alignment_prompt.txt",
        }
        with patch.dict(environ, self._complete_environment(), clear=True):
            return CliAnalysisServicesWiring(
                {}, prompt_file_overrides=prompt_file_overrides
            ).create_services()

    @staticmethod
    def _copy_packaged_prompts_root(destination: Path) -> Path:
        copytree(PROMPTS_ROOT, destination, ignore=ignore_patterns("v2", "__pycache__"))
        return destination

    def test_services_warms_up_language_model_is_false_when_startup_warmup_disabled(self):
        overrides = {"OLLAMA_WARMUP_ON_STARTUP": "false"}
        with patch.dict(environ, self._complete_environment(), clear=True):
            services = CliAnalysisServicesWiring(overrides).create_services()

        self.assertTrue(services.uses_local_language_model)
        self.assertFalse(services.warms_up_language_model)
