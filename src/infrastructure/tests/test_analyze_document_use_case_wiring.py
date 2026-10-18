from contextlib import closing
from os import environ
from os.path import join
from pathlib import Path
from sqlite3 import connect
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.ai_purpose import AiPurpose
from src.domain.enums.app_mode import AppMode
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.enums.section_name import SectionName
from src.domain.exceptions.settings_errors import SettingValueMissing
from src.domain.metrics.analysis_tracker import AnalysisTracker
from src.domain.metrics.audit_payload_policy import AuditPayloadPolicy
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.domain.quality.alignment_lines_extractor import AlignmentLinesExtractor
from src.domain.quality.contribution_observation_builder import ContributionObservationBuilder
from src.domain.quality.dimension_feedback_extractor import DimensionFeedbackExtractor
from src.domain.quality.dimension_score_extractor import DimensionScoreExtractor
from src.domain.quality.editorial_suitability_parser import EditorialSuitabilityParser
from src.domain.quality.quality_dimension_matcher import QualityDimensionMatcher
from src.domain.quality.quality_response_parser import QualityResponseParser
from src.domain.quality.suitability_field_extractor import SuitabilityFieldExtractor
from src.domain.quality.suitability_field_truncator import SuitabilityFieldTruncator
from src.domain.quality.suitability_verdict_matcher import SuitabilityVerdictMatcher
from src.domain.quality.trailing_score_line_locator import TrailingScoreLineLocator
from src.domain.structure.structure_validator import StructureValidator
from src.domain.tests.classification.fake_llm_generator_adapter import FakeLlmGeneratorAdapter
from src.domain.tests.dtos.editorial_norms_builder_for_test import (
    build_editorial_norms_for_test,
)
from src.domain.tests.structure.structure_norms_builder_for_test import (
    build_structure_norms_for_test,
)
from src.infrastructure.adapters.document.docx_citation_adapter import DocxCitationAdapter
from src.infrastructure.adapters.document.docx_eumic_adapter import DocxEumicAdapter
from src.infrastructure.adapters.grammar.language_tool_adapter import LanguageToolAdapter
from src.infrastructure.adapters.grammar.language_tool_settings import (
    LanguageToolSettings,
)
from src.infrastructure.adapters.llm_generator.audited_llm_generator_adapter import (
    AuditedLlmGeneratorAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_generator_adapter import (
    OllamaGeneratorAdapter,
)
from src.infrastructure.adapters.metrics.fail_safe_analysis_metrics_adapter import (
    FailSafeAnalysisMetricsAdapter,
)
from src.infrastructure.adapters.metrics.sqlite_analysis_metrics_adapter import (
    SqliteAnalysisMetricsAdapter,
)
from src.infrastructure.resources.prompts import PROMPTS_ROOT
from src.infrastructure.resources.prompts.classification import (
    PROMPTS_DIR as CLASSIFICATION_PROMPTS_DIR,
)
from src.infrastructure.tests.test_doubles.analyze_document_use_case_wiring_for_test import (
    AnalyzeDocumentUseCaseWiringForTest,
)
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.tests.test_doubles.complete_test_settings import (
    CompleteTestSettings,
)
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)
from src.infrastructure.wirings.external_llm_generator_loader import (
    ExternalLlmGeneratorLoader,
)


class TestAnalyzeDocumentUseCaseWiring(TestCase):
    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._settings_file_path = Path(self._temporary_directory.name) / "settings.toml"
        self._settings_file_path.write_text(CompleteTestSettings.toml_text(), encoding="utf-8")

    def test_create_use_case_returns_analyze_document_use_case_instance(self):
        result = AnalyzeDocumentUseCaseWiring().create_use_case()
        self.assertIsInstance(result, AnalyzeDocumentUseCase)

    def test_create_use_case_wires_all_domain_services(self):
        result = AnalyzeDocumentUseCaseWiring().create_use_case()
        self.assertIsNotNone(result._document_content_extractor)
        self.assertIsNotNone(result._citation_extractor)
        self.assertIsNotNone(result._document_format_inspector)
        self.assertIsNotNone(result._grammar_checker)
        self.assertIsNotNone(result._apa_validator)
        self.assertIsNotNone(result._article_classifier)
        self.assertIsNotNone(result._quality_analyzer)
        self.assertIsNotNone(result._structure_validator)
        self.assertIsNotNone(result._citation_matcher)
        self.assertIsNotNone(result._recommendation_builder)
        self.assertIsNotNone(result._analysis_tracker)

    def test_create_use_case_wires_analysis_tracker(self):
        result = AnalyzeDocumentUseCaseWiring().create_use_case()
        self.assertIsInstance(result._analysis_tracker, AnalysisTracker)

    def test_wiring_builds_document_format_inspection_port_with_editorial_norms(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)
            port = wiring._get_document_format_inspection_port()
        self.assertIsInstance(port, DocxEumicAdapter)
        assert isinstance(port, DocxEumicAdapter)
        self.assertEqual(
            port._minimum_words_for_abstract_check,
            CompleteTestSettings.expected_values()["eumic_min_words_for_abstract_check"],
        )
        self.assertEqual(port._norms, build_editorial_norms_for_test())

    def test_wiring_builds_structure_validator_with_editorial_norms_structure(self):
        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)
            validator = wiring._get_structure_validator()
        self.assertIsInstance(validator, StructureValidator)
        present = validator._extract_present_sections(["Resumen"])
        self.assertIn(SectionName.SUMMARY, present)
        self.assertEqual(validator._structure_norms, build_structure_norms_for_test())

    def test_wiring_builds_quality_response_parser_holding_collaborators(self):
        wiring = AnalyzeDocumentUseCaseWiring()
        quality_response_parser = wiring._get_quality_response_parser()
        self.assertIsInstance(quality_response_parser, QualityResponseParser)
        self.assertIsInstance(quality_response_parser._dimension_matcher, QualityDimensionMatcher)
        self.assertIsInstance(quality_response_parser._score_extractor, DimensionScoreExtractor)
        self.assertIsInstance(
            quality_response_parser._feedback_extractor, DimensionFeedbackExtractor
        )
        self.assertEqual(quality_response_parser._unscored_dimension.score, 7.0)
        self.assertEqual(quality_response_parser._unscored_dimension.feedback, "No disponible")

    def test_wiring_builds_quality_response_parser_holding_trailing_score_line_locator(self):
        wiring = AnalyzeDocumentUseCaseWiring()
        quality_response_parser = wiring._get_quality_response_parser()
        self.assertIsInstance(
            quality_response_parser._trailing_score_line_locator, TrailingScoreLineLocator
        )

    def test_wiring_builds_editorial_suitability_parser_holding_collaborators(self):
        wiring = AnalyzeDocumentUseCaseWiring()
        parser = wiring._get_editorial_suitability_parser()
        self.assertIsInstance(parser, EditorialSuitabilityParser)
        self.assertIsInstance(parser._field_extractor, SuitabilityFieldExtractor)
        self.assertIsInstance(parser._verdict_matcher, SuitabilityVerdictMatcher)
        self.assertIsInstance(parser._lines_extractor, AlignmentLinesExtractor)
        self.assertIsInstance(parser._field_truncator, SuitabilityFieldTruncator)
        self.assertIsInstance(parser._observation_builder, ContributionObservationBuilder)
        self.assertEqual(parser._phrase_max_length, 120)
        self.assertEqual(parser._justification_max_length, 120)
        self.assertEqual(parser._lines_max_length, 200)

    def test_article_classifier_and_quality_analyzer_wrap_the_same_ollama_generator(self):
        wiring = AnalyzeDocumentUseCaseWiring()
        use_case = wiring.create_use_case()
        classifier_generator = use_case._article_classifier._llm_generator
        quality_generator = use_case._quality_analyzer._llm_generator
        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertIsInstance(quality_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(classifier_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(quality_generator, AuditedLlmGeneratorAdapter)
        self.assertIs(
            classifier_generator._generator,
            quality_generator._generator,
        )

    def test_audited_llm_generators_configured_for_consumers(self):
        with patch.dict(environ, {"OLLAMA_MODEL_NAME": "custom-editorial-model"}):
            use_case = AnalyzeDocumentUseCaseWiring().create_use_case()

        classifier_generator = use_case._article_classifier._llm_generator
        quality_generator = use_case._quality_analyzer._llm_generator
        editorial_generator = (
            use_case._quality_analyzer._editorial_suitability_analyzer._llm_generator
        )

        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(classifier_generator._provider, AiProvider.OLLAMA)
        self.assertEqual(classifier_generator._model_name, "custom-editorial-model")
        self.assertEqual(classifier_generator._purpose, AiPurpose.ARTICLE_CLASSIFICATION)

        self.assertIsInstance(quality_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(quality_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(quality_generator._provider, AiProvider.OLLAMA)
        self.assertEqual(quality_generator._model_name, "custom-editorial-model")
        self.assertEqual(quality_generator._purpose, AiPurpose.QUALITY_ANALYSIS)

        self.assertIsInstance(editorial_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(editorial_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(editorial_generator._provider, AiProvider.OLLAMA)
        self.assertEqual(editorial_generator._model_name, "custom-editorial-model")
        self.assertEqual(editorial_generator._purpose, AiPurpose.EDITORIAL_SUITABILITY)

    def test_audited_adapters_and_tracker_share_metrics_port_and_audit_policy(self):
        use_case = AnalyzeDocumentUseCaseWiring().create_use_case()

        classifier_generator = use_case._article_classifier._llm_generator
        quality_generator = use_case._quality_analyzer._llm_generator
        editorial_generator = (
            use_case._quality_analyzer._editorial_suitability_analyzer._llm_generator
        )
        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertIsInstance(quality_generator, AuditedLlmGeneratorAdapter)
        self.assertIsInstance(editorial_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(classifier_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(quality_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(editorial_generator, AuditedLlmGeneratorAdapter)

        tracker_metrics_port = use_case._analysis_tracker._metrics_recorder._metrics_port

        self.assertIs(classifier_generator._metrics_port, quality_generator._metrics_port)
        self.assertIs(quality_generator._metrics_port, editorial_generator._metrics_port)
        self.assertIs(editorial_generator._metrics_port, tracker_metrics_port)

        self.assertIs(
            classifier_generator._audit_payload_policy,
            quality_generator._audit_payload_policy,
        )
        self.assertIs(
            quality_generator._audit_payload_policy,
            editorial_generator._audit_payload_policy,
        )

    def test_audit_payload_policy_mode_follows_app_mode(self):
        with patch.dict(environ, {"APP_MODE": "DEBUG"}):
            wiring = AnalyzeDocumentUseCaseWiring()
            policy = wiring._get_audit_payload_policy()
            self.assertEqual(policy._app_mode, AppMode.DEBUG)

        with patch.dict(environ, {"APP_MODE": "PROD"}):
            wiring = AnalyzeDocumentUseCaseWiring()
            policy = wiring._get_audit_payload_policy()
            self.assertEqual(policy._app_mode, AppMode.PROD)

    def test_shared_metrics_port_is_failsafe_sqlite_adapter_with_configured_path(self):
        with TemporaryDirectory() as temporary_directory:
            configured_database_path = join(temporary_directory, "test_metrics.db")
            with patch.dict(environ, {"METRICS_DATABASE_PATH": configured_database_path}):
                wiring = AnalyzeDocumentUseCaseWiring()
                metrics_port = wiring._get_analysis_metrics_port()
                self.assertIsInstance(metrics_port, FailSafeAnalysisMetricsAdapter)
                assert isinstance(metrics_port, FailSafeAnalysisMetricsAdapter)
                self.assertIsInstance(
                    metrics_port._analysis_metrics_port, SqliteAnalysisMetricsAdapter
                )
                assert isinstance(metrics_port._analysis_metrics_port, SqliteAnalysisMetricsAdapter)
                self.assertEqual(
                    metrics_port._analysis_metrics_port._database_path, configured_database_path
                )

    def _execute_classification_interaction_and_fetch_stored_row(
        self,
        app_mode: str,
        prompt: str,
        response_content: str,
    ) -> tuple[str, str, str, str, str, str]:
        with TemporaryDirectory() as temporary_directory:
            database_path = join(temporary_directory, "metrics.db")

            class InlineWiring(AnalyzeDocumentUseCaseWiring):
                def _get_ollama_generator(self) -> LlmGeneratorPort:
                    return FakeLlmGeneratorAdapter(responses=[response_content])

            with patch.dict(
                environ,
                {"METRICS_DATABASE_PATH": database_path, "APP_MODE": app_mode},
            ):
                use_case = InlineWiring().create_use_case()
                generator = use_case._article_classifier._llm_generator
                generation_result = generator.generate(prompt=prompt)
                self.assertEqual(generation_result, response_content)

            with closing(connect(database_path)) as connection:
                rows = connection.execute(
                    "SELECT analysis_id, provider, purpose, status, input_payload, output_payload FROM ai_interactions"
                ).fetchall()

            self.assertEqual(len(rows), 1)
            return rows[0]

    def test_audited_generator_records_redacted_payloads_in_sqlite_database_in_production_mode(
        self,
    ):
        prompt = "Document snippet for classification"
        response_content = "S4: NO\nS5: NO\nS6: NO"
        production_policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        expected_input_payload = production_policy.apply(prompt)
        expected_output_payload = production_policy.apply(response_content)

        (
            analysis_id,
            provider,
            purpose,
            status,
            input_payload,
            output_payload,
        ) = self._execute_classification_interaction_and_fetch_stored_row(
            app_mode="PROD",
            prompt=prompt,
            response_content=response_content,
        )

        self.assertEqual(analysis_id, "unassigned")
        self.assertEqual(provider, AiProvider.OLLAMA.value)
        self.assertEqual(purpose, AiPurpose.ARTICLE_CLASSIFICATION.value)
        self.assertEqual(status, ExecutionStatus.SUCCESS.value)
        self.assertEqual(input_payload, expected_input_payload)
        self.assertEqual(output_payload, expected_output_payload)

    def test_audited_generator_records_full_payloads_in_sqlite_database_in_debug_mode(self):
        prompt = "Document snippet for debug classification"
        response_content = "S4: YES\nS5: NO\nS6: NO"

        (
            analysis_id,
            provider,
            purpose,
            status,
            input_payload,
            output_payload,
        ) = self._execute_classification_interaction_and_fetch_stored_row(
            app_mode="DEBUG",
            prompt=prompt,
            response_content=response_content,
        )

        self.assertEqual(analysis_id, "unassigned")
        self.assertEqual(provider, AiProvider.OLLAMA.value)
        self.assertEqual(purpose, AiPurpose.ARTICLE_CLASSIFICATION.value)
        self.assertEqual(status, ExecutionStatus.SUCCESS.value)
        self.assertEqual(input_payload, prompt)
        self.assertEqual(output_payload, response_content)

    @staticmethod
    def _complete_environment(overrides: dict[str, str] | None = None) -> dict[str, str]:
        environment = {
            **CompleteTestEnvironment.application_variables(),
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }
        if overrides:
            environment.update(overrides)
        return environment

    def _create_use_case_from_test_settings(self) -> AnalyzeDocumentUseCase:
        with patch.dict(environ, self._complete_environment(), clear=True):
            return AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path).create_use_case()

    def test_env_var_overrides_quality_threshold(self):
        with patch.dict(environ, {"QUALITY_THRESHOLD": "6.5"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = (
            result._recommendation_builder._recommendation_settings
        )
        self.assertAlmostEqual(settings.quality_threshold, 6.5)

    def test_env_var_overrides_grammar_threshold(self):
        with patch.dict(environ, {"GRAMMAR_THRESHOLD": "5.0"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = (
            result._recommendation_builder._recommendation_settings
        )
        self.assertAlmostEqual(settings.grammar_threshold, 5.0)

    def test_env_var_overrides_critical_quality_threshold(self):
        with patch.dict(environ, {"CRITICAL_QUALITY_THRESHOLD": "4.0"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = (
            result._recommendation_builder._recommendation_settings
        )
        self.assertAlmostEqual(settings.critical_quality_threshold, 4.0)

    def test_env_var_overrides_critical_grammar_threshold(self):
        with patch.dict(environ, {"CRITICAL_GRAMMAR_THRESHOLD": "4.0"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = (
            result._recommendation_builder._recommendation_settings
        )
        self.assertAlmostEqual(settings.critical_grammar_threshold, 4.0)

    def test_env_var_overrides_structure_max_header_length(self):
        with patch.dict(environ, {"STRUCTURE_MAX_HEADER_LENGTH": "50"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        self.assertEqual(result._structure_validator._max_header_length, 50)

    def test_env_var_overrides_citation_max_author_name_length(self):
        with patch.dict(environ, {"CITATION_MAX_AUTHOR_NAME_LENGTH": "5"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        port = result._citation_extractor._citation_extraction_port
        self.assertIsInstance(port, DocxCitationAdapter)
        assert isinstance(port, DocxCitationAdapter)
        self.assertEqual(port._max_author_name_length, 5)

    def test_env_var_overrides_grammar_max_replacements(self):
        with patch.dict(environ, {"GRAMMAR_MAX_REPLACEMENTS": "2"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        port = result._grammar_checker._grammar_check_port
        self.assertIsInstance(port, LanguageToolAdapter)
        assert isinstance(port, LanguageToolAdapter)
        self.assertEqual(port._language_tool_settings.max_replacements, 2)

    def test_default_grammar_adapter_parameters_when_env_vars_absent(self):
        expected = CompleteTestSettings.expected_values()
        result = self._create_use_case_from_test_settings()
        port = result._grammar_checker._grammar_check_port
        self.assertIsInstance(port, LanguageToolAdapter)
        assert isinstance(port, LanguageToolAdapter)
        self.assertIsInstance(port._language_tool_settings, LanguageToolSettings)
        self.assertEqual(
            port._language_tool_settings.max_replacements, expected["grammar_max_replacements"]
        )

    def test_env_vars_override_grammar_adapter_parameters(self):
        with patch.dict(environ, {"GRAMMAR_MAX_REPLACEMENTS": "5"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        port = result._grammar_checker._grammar_check_port
        self.assertIsInstance(port, LanguageToolAdapter)
        assert isinstance(port, LanguageToolAdapter)
        self.assertIsInstance(port._language_tool_settings, LanguageToolSettings)
        self.assertEqual(port._language_tool_settings.max_replacements, 5)

    def test_missing_ollama_think_raises_setting_value_missing(self):
        env_without = {k: v for k, v in environ.items() if k != "OLLAMA_THINK"}
        with patch.dict(environ, env_without, clear=True):
            with self.assertRaises(SettingValueMissing):
                AnalyzeDocumentUseCaseWiring().create_use_case()

    def test_env_var_overrides_ollama_think(self):
        with patch.dict(environ, {"OLLAMA_THINK": "true"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        audited_generator = result._article_classifier._llm_generator
        assert isinstance(audited_generator, AuditedLlmGeneratorAdapter)
        generator = audited_generator._generator
        self.assertIsInstance(generator, OllamaGeneratorAdapter)
        assert isinstance(generator, OllamaGeneratorAdapter)
        self.assertTrue(generator._think)

    def test_missing_ollama_model_keep_alive_raises_setting_value_missing(self):
        env_without = {k: v for k, v in environ.items() if k != "OLLAMA_MODEL_KEEP_ALIVE"}
        with patch.dict(environ, env_without, clear=True):
            with self.assertRaises(SettingValueMissing):
                AnalyzeDocumentUseCaseWiring().create_use_case()

    def test_env_var_overrides_ollama_keep_alive(self):
        with patch.dict(environ, {"OLLAMA_MODEL_KEEP_ALIVE": "30m"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        audited_generator = result._article_classifier._llm_generator
        assert isinstance(audited_generator, AuditedLlmGeneratorAdapter)
        generator = audited_generator._generator
        self.assertIsInstance(generator, OllamaGeneratorAdapter)
        assert isinstance(generator, OllamaGeneratorAdapter)
        self.assertEqual(generator._keep_alive, "30m")

    def test_default_ollama_num_ctx_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "OLLAMA_NUM_CTX"}
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        audited_generator = result._article_classifier._llm_generator
        assert isinstance(audited_generator, AuditedLlmGeneratorAdapter)
        generator = audited_generator._generator
        self.assertIsInstance(generator, OllamaGeneratorAdapter)
        assert isinstance(generator, OllamaGeneratorAdapter)
        self.assertIsNone(generator._num_ctx)

    def test_env_var_overrides_ollama_num_ctx(self):
        with patch.dict(environ, {"OLLAMA_NUM_CTX": "16384"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        audited_generator = result._article_classifier._llm_generator
        assert isinstance(audited_generator, AuditedLlmGeneratorAdapter)
        generator = audited_generator._generator
        self.assertIsInstance(generator, OllamaGeneratorAdapter)
        assert isinstance(generator, OllamaGeneratorAdapter)
        self.assertEqual(generator._num_ctx, 16384)

    def test_editorial_suitability_analyzer_uses_default_generation_options(self):
        expected = CompleteTestSettings.expected_values()
        use_case = self._create_use_case_from_test_settings()
        analyzer = use_case._quality_analyzer._editorial_suitability_analyzer
        self.assertAlmostEqual(analyzer._temperature, expected["article_classifier_temperature"])
        self.assertEqual(analyzer._num_predict, expected["article_classifier_num_predict"])

    def test_env_vars_override_editorial_suitability_generation_options(self):
        with patch.dict(
            environ,
            {"ARTICLE_CLASSIFIER_TEMPERATURE": "0.4", "ARTICLE_CLASSIFIER_NUM_PREDICT": "512"},
        ):
            use_case = AnalyzeDocumentUseCaseWiring().create_use_case()
        analyzer = use_case._quality_analyzer._editorial_suitability_analyzer
        self.assertAlmostEqual(analyzer._temperature, 0.4)
        self.assertEqual(analyzer._num_predict, 512)

    def test_default_wiring_uses_ollama_generator_and_provider(self):
        use_case = AnalyzeDocumentUseCaseWiring().create_use_case()
        classifier_generator = use_case._article_classifier._llm_generator
        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(classifier_generator._provider, AiProvider.OLLAMA)
        self.assertIsInstance(classifier_generator._generator, OllamaGeneratorAdapter)
        assert isinstance(classifier_generator._generator, OllamaGeneratorAdapter)

    def test_debug_mode_with_claude_provider_wires_external_llm_generator(self):
        fake_generator = FakeLlmGeneratorAdapter(responses=["test response"])
        with patch.dict(
            environ,
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "claude",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
            },
        ):
            with patch.object(
                ExternalLlmGeneratorLoader,
                "load",
                return_value=fake_generator,
            ) as mock_load:
                use_case = AnalyzeDocumentUseCaseWiring().create_use_case()

        classifier_generator = use_case._article_classifier._llm_generator
        quality_generator = use_case._quality_analyzer._llm_generator
        editorial_generator = (
            use_case._quality_analyzer._editorial_suitability_analyzer._llm_generator
        )

        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(classifier_generator._provider, AiProvider.CLAUDE)
        self.assertEqual(classifier_generator._model_name, "claude-3-7-sonnet")
        self.assertIs(classifier_generator._generator, fake_generator)

        self.assertIsInstance(quality_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(quality_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(quality_generator._provider, AiProvider.CLAUDE)
        self.assertEqual(quality_generator._model_name, "claude-3-7-sonnet")
        self.assertIs(quality_generator._generator, fake_generator)

        self.assertIsInstance(editorial_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(editorial_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(editorial_generator._provider, AiProvider.CLAUDE)
        self.assertEqual(editorial_generator._model_name, "claude-3-7-sonnet")
        self.assertIs(editorial_generator._generator, fake_generator)

        mock_load.assert_called_once_with(
            provider=AiProvider.CLAUDE,
            model_name="claude-3-7-sonnet",
            think=False,
        )

    def test_debug_mode_with_claude_provider_forwards_external_llm_think_true_to_loader(self):
        fake_generator = FakeLlmGeneratorAdapter(responses=["test response"])
        with patch.dict(
            environ,
            {
                "APP_MODE": "DEBUG",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "claude",
                "EXTERNAL_LLM_MODEL_NAME": "claude-3-7-sonnet",
                "EXTERNAL_LLM_THINK": "true",
            },
        ):
            with patch.object(
                ExternalLlmGeneratorLoader,
                "load",
                return_value=fake_generator,
            ) as mock_load:
                AnalyzeDocumentUseCaseWiring().create_use_case()

        mock_load.assert_called_once_with(
            provider=AiProvider.CLAUDE,
            model_name="claude-3-7-sonnet",
            think=True,
        )

    def test_production_mode_with_claude_provider_stays_ollama(self):
        with patch.dict(
            environ,
            {
                "APP_MODE": "PROD",
                "USE_EXTERNAL_LLM": "true",
                "LLM_PROVIDER": "claude",
            },
        ):
            with patch.object(
                ExternalLlmGeneratorLoader,
                "load",
            ) as mock_load:
                use_case = AnalyzeDocumentUseCaseWiring().create_use_case()

        classifier_generator = use_case._article_classifier._llm_generator
        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        assert isinstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(classifier_generator._provider, AiProvider.OLLAMA)
        self.assertIsInstance(classifier_generator._generator, OllamaGeneratorAdapter)
        assert isinstance(classifier_generator._generator, OllamaGeneratorAdapter)
        mock_load.assert_not_called()

    def test_read_prompt_text_reads_text_resource(self):
        wiring = AnalyzeDocumentUseCaseWiring()
        text = wiring._read_prompt_text(
            directory=CLASSIFICATION_PROMPTS_DIR,
            filename="s4_s5_s6_signal_prompt.txt",
        )
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)


class TestAnalyzeDocumentUseCaseWiringPromptsRoot(TestCase):
    PROMPT_RELATIVE_PATHS = (
        "classification/s4_s5_s6_signal_prompt.txt",
        "quality/alignment_prompt.txt",
        "quality/argumentation_conclusions_prompt.txt",
        "quality/clarity_coherence_prompt.txt",
        "quality/contribution_prompt.txt",
        "quality/research_lines.txt",
    )

    def test_create_use_case_reads_prompt_templates_from_custom_prompts_root(self):
        prompts_root = self._write_prompts_root(content_prefix="custom")
        with patch.dict(environ, self._complete_environment(), clear=True):
            use_case = AnalyzeDocumentUseCaseWiring(prompts_root=prompts_root).create_use_case()

        self.assertEqual(
            use_case._article_classifier._signal_prompt_template,
            "custom s4_s5_s6_signal_prompt",
        )
        self.assertEqual(
            use_case._quality_analyzer._clarity_coherence_prompt_template,
            "custom clarity_coherence_prompt",
        )
        self.assertEqual(
            use_case._quality_analyzer._argumentation_conclusions_prompt_template,
            "custom argumentation_conclusions_prompt",
        )
        suitability_analyzer = use_case._quality_analyzer._editorial_suitability_analyzer
        self.assertEqual(
            suitability_analyzer._contribution_prompt_template,
            "custom contribution_prompt",
        )
        self.assertEqual(
            suitability_analyzer._alignment_prompt_template,
            "custom alignment_prompt",
        )
        self.assertEqual(suitability_analyzer._research_lines, "custom research_lines")

    def test_create_use_case_loads_renamed_v2_prompt_set_from_its_root(self):
        v2_prompts_root = PROMPTS_ROOT / "v2"
        with patch.dict(environ, self._complete_environment(), clear=True):
            use_case = AnalyzeDocumentUseCaseWiring(prompts_root=v2_prompts_root).create_use_case()

        self.assertEqual(
            use_case._article_classifier._signal_prompt_template,
            (v2_prompts_root / "classification" / "s4_s5_s6_signal_prompt.txt").read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(
            use_case._quality_analyzer._clarity_coherence_prompt_template,
            (v2_prompts_root / "quality" / "clarity_coherence_prompt.txt").read_text(
                encoding="utf-8"
            ),
        )

    @staticmethod
    def _complete_environment() -> dict[str, str]:
        return {
            **CompleteTestEnvironment.application_variables(),
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }

    def _write_prompts_root(self, content_prefix: str) -> Path:
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        prompts_root = Path(temporary_directory.name)
        for relative_path in self.PROMPT_RELATIVE_PATHS:
            prompt_path = prompts_root / relative_path
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(f"{content_prefix} {prompt_path.stem}", encoding="utf-8")
        return prompts_root
