from contextlib import closing
from os import environ
from os.path import join
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
from src.domain.metrics.analysis_tracker import AnalysisTracker
from src.domain.metrics.audit_payload_policy import AuditPayloadPolicy
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.domain.tests.classification.fake_llm_generator_adapter import FakeLlmGeneratorAdapter
from src.infrastructure.adapters.document.docx_citation_adapter import DocxCitationAdapter
from src.infrastructure.adapters.grammar.language_tool_adapter import LanguageToolAdapter
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
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)
from src.infrastructure.wirings.external_llm_generator_loader import (
    ExternalLlmGeneratorLoader,
)


class TestAnalyzeDocumentUseCaseWiring(TestCase):
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

    def test_article_classifier_and_quality_analyzer_wrap_the_same_ollama_generator(self):
        wiring = AnalyzeDocumentUseCaseWiring()
        use_case = wiring.create_use_case()
        classifier_generator = use_case._article_classifier._llm_generator
        quality_generator = use_case._quality_analyzer._llm_generator
        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertIsInstance(quality_generator, AuditedLlmGeneratorAdapter)
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
        self.assertEqual(classifier_generator._provider, AiProvider.OLLAMA)
        self.assertEqual(classifier_generator._model_name, "custom-editorial-model")
        self.assertEqual(classifier_generator._purpose, AiPurpose.ARTICLE_CLASSIFICATION)

        self.assertIsInstance(quality_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(quality_generator._provider, AiProvider.OLLAMA)
        self.assertEqual(quality_generator._model_name, "custom-editorial-model")
        self.assertEqual(quality_generator._purpose, AiPurpose.QUALITY_ANALYSIS)

        self.assertIsInstance(editorial_generator, AuditedLlmGeneratorAdapter)
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

        environment_without_app_mode = {
            key: value for key, value in environ.items() if key != "APP_MODE"
        }
        environment_without_app_mode.update(self.REQUIRED_ENVIRONMENT)
        with patch.dict(environ, environment_without_app_mode, clear=True):
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
                self.assertIsInstance(
                    metrics_port._analysis_metrics_port, SqliteAnalysisMetricsAdapter
                )
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

    REQUIRED_ENVIRONMENT = {
        "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
        "LOG_FILE_PATH": "/custom/path/silvina.log",
    }

    RECOMMENDATION_ENV_VARS = {
        "PUBLISH_THRESHOLD",
        "QUALITY_THRESHOLD",
        "GRAMMAR_THRESHOLD",
        "DIMENSION_THRESHOLD",
        "CITATION_MATCH_THRESHOLD",
        "CRITICAL_CITATION_MATCH_THRESHOLD",
        "CITATION_COUNT_THRESHOLD",
        "CLASSIFICATION_CONFIDENCE_THRESHOLD",
        "CRITICAL_QUALITY_THRESHOLD",
        "CRITICAL_GRAMMAR_THRESHOLD",
    }

    def test_env_var_overrides_quality_threshold(self):
        with patch.dict(environ, {"QUALITY_THRESHOLD": "6.5"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.quality_threshold, 6.5)

    def test_env_var_overrides_grammar_threshold(self):
        with patch.dict(environ, {"GRAMMAR_THRESHOLD": "5.0"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.grammar_threshold, 5.0)

    def test_default_thresholds_when_env_vars_absent(self):
        env_without = {k: v for k, v in environ.items() if k not in self.RECOMMENDATION_ENV_VARS}
        env_without.update(self.REQUIRED_ENVIRONMENT)
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.publish_threshold, 7.0)
        self.assertAlmostEqual(settings.quality_threshold, 7.0)
        self.assertAlmostEqual(settings.grammar_threshold, 7.0)
        self.assertAlmostEqual(settings.dimension_threshold, 6.0)
        self.assertAlmostEqual(settings.citation_match_threshold, 90.0)
        self.assertAlmostEqual(settings.critical_citation_match_threshold, 50.0)
        self.assertEqual(settings.citation_count_threshold, 10)
        self.assertAlmostEqual(settings.classification_confidence_threshold, 0.7)
        self.assertAlmostEqual(settings.critical_quality_threshold, 5.0)
        self.assertAlmostEqual(settings.critical_grammar_threshold, 5.0)

    def test_env_var_overrides_critical_quality_threshold(self):
        with patch.dict(environ, {"CRITICAL_QUALITY_THRESHOLD": "4.0"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.critical_quality_threshold, 4.0)

    def test_env_var_overrides_critical_grammar_threshold(self):
        with patch.dict(environ, {"CRITICAL_GRAMMAR_THRESHOLD": "4.0"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.critical_grammar_threshold, 4.0)

    def test_env_var_overrides_structure_max_header_length(self):
        with patch.dict(environ, {"STRUCTURE_MAX_HEADER_LENGTH": "50"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        self.assertEqual(result._structure_validator._max_header_length, 50)

    def test_default_structure_max_header_length_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "STRUCTURE_MAX_HEADER_LENGTH"}
        env_without.update(self.REQUIRED_ENVIRONMENT)
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        self.assertEqual(result._structure_validator._max_header_length, 100)

    def test_env_var_overrides_citation_max_author_name_length(self):
        with patch.dict(environ, {"CITATION_MAX_AUTHOR_NAME_LENGTH": "5"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        port = result._citation_extractor._citation_extraction_port
        self.assertIsInstance(port, DocxCitationAdapter)
        self.assertEqual(port._max_author_name_length, 5)

    def test_default_citation_max_author_name_length_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "CITATION_MAX_AUTHOR_NAME_LENGTH"}
        env_without.update(self.REQUIRED_ENVIRONMENT)
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        port = result._citation_extractor._citation_extraction_port
        self.assertIsInstance(port, DocxCitationAdapter)
        self.assertEqual(port._max_author_name_length, 100)

    def test_env_var_overrides_grammar_max_replacements(self):
        with patch.dict(environ, {"GRAMMAR_MAX_REPLACEMENTS": "2"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        port = result._grammar_checker._grammar_check_port
        self.assertIsInstance(port, LanguageToolAdapter)
        self.assertEqual(port._max_replacements, 2)

    def test_default_grammar_max_replacements_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "GRAMMAR_MAX_REPLACEMENTS"}
        env_without.update(self.REQUIRED_ENVIRONMENT)
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        port = result._grammar_checker._grammar_check_port
        self.assertIsInstance(port, LanguageToolAdapter)
        self.assertEqual(port._max_replacements, 3)

    def test_default_ollama_think_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "OLLAMA_THINK"}
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        generator = result._article_classifier._llm_generator._generator
        self.assertIsInstance(generator, OllamaGeneratorAdapter)
        self.assertFalse(generator._think)

    def test_env_var_overrides_ollama_think(self):
        with patch.dict(environ, {"OLLAMA_THINK": "true"}):
            result = AnalyzeDocumentUseCaseWiring().create_use_case()
        generator = result._article_classifier._llm_generator._generator
        self.assertIsInstance(generator, OllamaGeneratorAdapter)
        self.assertTrue(generator._think)

    def test_default_wiring_uses_ollama_generator_and_provider(self):
        use_case = AnalyzeDocumentUseCaseWiring().create_use_case()
        classifier_generator = use_case._article_classifier._llm_generator
        self.assertIsInstance(classifier_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(classifier_generator._provider, AiProvider.OLLAMA)
        self.assertIsInstance(classifier_generator._generator, OllamaGeneratorAdapter)

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
        self.assertEqual(classifier_generator._provider, AiProvider.CLAUDE)
        self.assertEqual(classifier_generator._model_name, "claude-3-7-sonnet")
        self.assertIs(classifier_generator._generator, fake_generator)

        self.assertIsInstance(quality_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(quality_generator._provider, AiProvider.CLAUDE)
        self.assertEqual(quality_generator._model_name, "claude-3-7-sonnet")
        self.assertIs(quality_generator._generator, fake_generator)

        self.assertIsInstance(editorial_generator, AuditedLlmGeneratorAdapter)
        self.assertEqual(editorial_generator._provider, AiProvider.CLAUDE)
        self.assertEqual(editorial_generator._model_name, "claude-3-7-sonnet")
        self.assertIs(editorial_generator._generator, fake_generator)

        mock_load.assert_called_once_with(
            provider=AiProvider.CLAUDE,
            model_name="claude-3-7-sonnet",
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
        self.assertEqual(classifier_generator._provider, AiProvider.OLLAMA)
        self.assertIsInstance(classifier_generator._generator, OllamaGeneratorAdapter)
        mock_load.assert_not_called()
