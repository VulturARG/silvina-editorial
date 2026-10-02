from typing import get_args
from unittest import TestCase

from fastapi.params import Depends

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.export_report_use_case import ExportReportUseCase
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
    get_analysis_cancellation_port,
    get_analyze_document_use_case,
    get_env_config,
    get_export_report_use_case,
    get_json_export_report_use_case,
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

    def test_reset_dependencies_creates_fresh_instances(self):
        original_analyze = get_analyze_document_use_case()
        original_export = get_export_report_use_case()
        original_json = get_json_export_report_use_case()
        original_env = get_env_config()
        original_cancellation = get_analysis_cancellation_port()

        reset_dependencies()

        new_analyze = get_analyze_document_use_case()
        new_export = get_export_report_use_case()
        new_json = get_json_export_report_use_case()
        new_env = get_env_config()
        new_cancellation = get_analysis_cancellation_port()

        self.assertIsNot(original_analyze, new_analyze)
        self.assertIsNot(original_export, new_export)
        self.assertIsNot(original_json, new_json)
        self.assertIsNot(original_env, new_env)
        self.assertIsNot(original_cancellation, new_cancellation)
