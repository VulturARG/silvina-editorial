from typing import get_args
from unittest import TestCase
from unittest.mock import patch

from fastapi.params import Depends
from fastapi.templating import Jinja2Templates

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.export_report_use_case import ExportReportUseCase
from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.domain.metrics.analysis_cancellation_port import AnalysisCancellationPort
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.adapters.report.json_report_adapter import JsonReportAdapter
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.fastapi.src.config.dependencies import (
    AnalysisCancellationPortDep,
    AnalyzeUseCaseDep,
    EnvConfigDep,
    ExportReportUseCaseDep,
    JsonReportUseCaseDep,
    TemplatesDep,
    get_analysis_cancellation_port,
    get_analyze_document_use_case,
    get_env_config,
    get_export_report_use_case,
    get_json_export_report_use_case,
    get_templates,
    get_warm_up_language_model_use_case,
    initialize_dependencies,
    reset_dependencies,
)


class TestFastApiDependencies(TestCase):
    """Unit tests for FastAPI dependency injection providers and singleton dependencies."""

    def test_get_analyze_document_use_case_returns_singleton_instance(self):
        first_instance = get_analyze_document_use_case()
        second_instance = get_analyze_document_use_case()

        self.assertIsInstance(first_instance, AnalyzeDocumentUseCase)
        self.assertIs(first_instance, second_instance)

    def test_get_export_report_use_case_returns_singleton_docx_instance(self):
        first_instance = get_export_report_use_case()
        second_instance = get_export_report_use_case()

        self.assertIsInstance(first_instance, ExportReportUseCase)
        self.assertIsInstance(first_instance._report_export_port, DocxReportAdapter)
        self.assertIs(first_instance, second_instance)

    def test_get_json_export_report_use_case_returns_singleton_json_instance(self):
        first_instance = get_json_export_report_use_case()
        second_instance = get_json_export_report_use_case()

        self.assertIsInstance(first_instance, ExportReportUseCase)
        self.assertIsInstance(first_instance._report_export_port, JsonReportAdapter)
        self.assertIs(first_instance, second_instance)

    def test_get_env_config_returns_singleton_instance(self):
        first_instance = get_env_config()
        second_instance = get_env_config()

        self.assertIsInstance(first_instance, EnvConfig)
        self.assertIs(first_instance, second_instance)

    def test_get_analysis_cancellation_port_returns_singleton_instance(self):
        first_instance = get_analysis_cancellation_port()
        second_instance = get_analysis_cancellation_port()

        self.assertIsInstance(first_instance, AnalysisCancellationPort)
        self.assertIs(first_instance, second_instance)

    def test_get_templates_returns_singleton_instance_with_configured_globals(self):
        first_instance = get_templates()
        second_instance = get_templates()
        environment_configuration = get_env_config()

        self.assertIsInstance(first_instance, Jinja2Templates)
        self.assertIs(first_instance, second_instance)
        self.assertIn("app_name", first_instance.env.globals)
        self.assertIn("app_version", first_instance.env.globals)
        self.assertIn("inline_bold", first_instance.env.filters)
        self.assertIn("dimension_label", first_instance.env.filters)
        self.assertEqual(
            first_instance.env.globals["app_name"],
            environment_configuration.silvina_app_name,
        )
        self.assertEqual(
            first_instance.env.globals["app_version"],
            environment_configuration.silvina_version,
        )

    def test_dependency_annotations_map_to_expected_dependencies(self):
        analyze_type, analyze_dep = get_args(AnalyzeUseCaseDep)
        self.assertEqual(analyze_type, AnalyzeDocumentUseCase)
        self.assertIsInstance(analyze_dep, Depends)
        self.assertIs(analyze_dep.dependency, get_analyze_document_use_case)

        export_type, export_dep = get_args(ExportReportUseCaseDep)
        self.assertEqual(export_type, ExportReportUseCase)
        self.assertIsInstance(export_dep, Depends)
        self.assertIs(export_dep.dependency, get_export_report_use_case)

        json_type, json_dep = get_args(JsonReportUseCaseDep)
        self.assertEqual(json_type, ExportReportUseCase)
        self.assertIsInstance(json_dep, Depends)
        self.assertIs(json_dep.dependency, get_json_export_report_use_case)

        env_type, env_dep = get_args(EnvConfigDep)
        self.assertEqual(env_type, EnvConfig)
        self.assertIsInstance(env_dep, Depends)
        self.assertIs(env_dep.dependency, get_env_config)

        cancellation_type, cancellation_dep = get_args(AnalysisCancellationPortDep)
        self.assertEqual(cancellation_type, AnalysisCancellationPort)
        self.assertIsInstance(cancellation_dep, Depends)
        self.assertIs(cancellation_dep.dependency, get_analysis_cancellation_port)

        templates_type, templates_dependency = get_args(TemplatesDep)
        self.assertEqual(templates_type, Jinja2Templates)
        self.assertIsInstance(templates_dependency, Depends)
        self.assertIs(templates_dependency.dependency, get_templates)

    def test_reset_dependencies_creates_fresh_instances(self):
        original_analyze = get_analyze_document_use_case()
        original_export = get_export_report_use_case()
        original_json = get_json_export_report_use_case()
        original_env = get_env_config()
        original_cancellation = get_analysis_cancellation_port()
        original_templates = get_templates()

        reset_dependencies()

        new_analyze = get_analyze_document_use_case()
        new_export = get_export_report_use_case()
        new_json = get_json_export_report_use_case()
        new_env = get_env_config()
        new_cancellation = get_analysis_cancellation_port()
        new_templates = get_templates()

        self.assertIsNot(original_analyze, new_analyze)
        self.assertIsNot(original_export, new_export)
        self.assertIsNot(original_json, new_json)
        self.assertIsNot(original_env, new_env)
        self.assertIsNot(original_cancellation, new_cancellation)
        self.assertIsNot(original_templates, new_templates)

    def test_reset_dependencies_preserves_template_globals(self):
        reset_dependencies()
        templates = get_templates()
        environment_configuration = get_env_config()

        self.assertIn("app_name", templates.env.globals)
        self.assertIn("app_version", templates.env.globals)
        self.assertIn("inline_bold", templates.env.filters)
        self.assertIn("dimension_label", templates.env.filters)
        self.assertEqual(
            templates.env.globals["app_name"],
            environment_configuration.silvina_app_name,
        )
        self.assertEqual(
            templates.env.globals["app_version"],
            environment_configuration.silvina_version,
        )

    def test_get_warm_up_language_model_use_case_returns_singleton_instance(self):
        first_instance = get_warm_up_language_model_use_case()
        second_instance = get_warm_up_language_model_use_case()

        self.assertIsInstance(first_instance, WarmUpLanguageModelUseCase)
        self.assertIs(first_instance, second_instance)

    @patch("src.infrastructure.fastapi.src.config.dependencies.WarmUpLanguageModelUseCaseWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.AnalysisCancellationWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.JsonReportWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.ExportReportWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.AnalyzeDocumentUseCaseWiring")
    def test_reset_dependencies_does_not_instantiate_wirings(
        self,
        mock_analyze_wiring,
        mock_export_wiring,
        mock_json_wiring,
        mock_cancellation_wiring,
        mock_warm_up_wiring,
    ):
        reset_dependencies()

        mock_analyze_wiring.assert_not_called()
        mock_export_wiring.assert_not_called()
        mock_json_wiring.assert_not_called()
        mock_cancellation_wiring.assert_not_called()
        mock_warm_up_wiring.assert_not_called()

    @patch("src.infrastructure.fastapi.src.config.dependencies.WarmUpLanguageModelUseCaseWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.AnalysisCancellationWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.JsonReportWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.ExportReportWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.AnalyzeDocumentUseCaseWiring")
    def test_getters_instantiate_lazily_and_cache_instances(
        self,
        mock_analyze_wiring,
        mock_export_wiring,
        mock_json_wiring,
        mock_cancellation_wiring,
        mock_warm_up_wiring,
    ):
        reset_dependencies()

        first_analyze = get_analyze_document_use_case()
        second_analyze = get_analyze_document_use_case()
        mock_analyze_wiring.return_value.create_use_case.assert_called_once()
        self.assertIs(first_analyze, second_analyze)

        first_export = get_export_report_use_case()
        second_export = get_export_report_use_case()
        mock_export_wiring.return_value.create_use_case.assert_called_once()
        self.assertIs(first_export, second_export)

        first_json = get_json_export_report_use_case()
        second_json = get_json_export_report_use_case()
        mock_json_wiring.return_value.create_use_case.assert_called_once()
        self.assertIs(first_json, second_json)

        first_cancellation = get_analysis_cancellation_port()
        second_cancellation = get_analysis_cancellation_port()
        mock_cancellation_wiring.return_value.get_analysis_cancellation_port.assert_called_once()
        self.assertIs(first_cancellation, second_cancellation)

        first_warm_up = get_warm_up_language_model_use_case()
        second_warm_up = get_warm_up_language_model_use_case()
        mock_warm_up_wiring.return_value.get_warm_up_language_model_use_case.assert_called_once()
        self.assertIs(first_warm_up, second_warm_up)

    @patch("src.infrastructure.fastapi.src.config.dependencies.WarmUpLanguageModelUseCaseWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.AnalysisCancellationWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.JsonReportWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.ExportReportWiring")
    @patch("src.infrastructure.fastapi.src.config.dependencies.AnalyzeDocumentUseCaseWiring")
    def test_initialize_dependencies_builds_all_five_singletons(
        self,
        mock_analyze_wiring,
        mock_export_wiring,
        mock_json_wiring,
        mock_cancellation_wiring,
        mock_warm_up_wiring,
    ):
        reset_dependencies()
        initialize_dependencies()

        mock_analyze_wiring.return_value.create_use_case.assert_called_once()
        mock_export_wiring.return_value.create_use_case.assert_called_once()
        mock_json_wiring.return_value.create_use_case.assert_called_once()
        mock_cancellation_wiring.return_value.get_analysis_cancellation_port.assert_called_once()
        mock_warm_up_wiring.return_value.get_warm_up_language_model_use_case.assert_called_once()
