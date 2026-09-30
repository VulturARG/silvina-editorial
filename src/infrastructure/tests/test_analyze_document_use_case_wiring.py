# pyright: reportAttributeAccessIssue=none
from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.laya.laya_decision_maker import LayaDecisionMaker
from src.domain.laya.laya_text_sampler import LayaTextSampler
from src.infrastructure.adapters.laya.laya_decision_adapter import LayaDecisionAdapter
from src.infrastructure.tests.test_doubles.analyze_document_use_case_wiring_for_test import (
    AnalyzeDocumentUseCaseWiringForTest,
)
from src.infrastructure.tests.test_doubles.fake_laya_agent import FakeLayaAgent
from src.infrastructure.wirings.analyze_document_use_case_wiring import AnalyzeDocumentUseCaseWiring


class TestAnalyzeDocumentUseCaseWiring(TestCase):
    def test_create_use_case_returns_analyze_document_use_case_instance(self):
        result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        self.assertIsInstance(result, AnalyzeDocumentUseCase)

    def test_create_use_case_wires_all_domain_services(self):
        result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
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

    def test_create_use_case_wires_laya_decision_maker(self):
        result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        self.assertIsInstance(result._laya_decision_maker, LayaDecisionMaker)
        self.assertIsInstance(result._laya_decision_maker._text_sampler, LayaTextSampler)

    def test_laya_text_sampler_uses_env_settings(self):
        with patch.dict(environ, {"LAYA_TEXT_SAMPLE_CHARACTER_LIMIT": "7000"}):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        text_sampler = result._laya_decision_maker._text_sampler
        self.assertEqual(text_sampler._text_sample_settings.text_sample_character_limit, 7000)

    def test_laya_decision_port_loads_configured_checkpoint_and_questions(self):
        fake_agent = FakeLayaAgent(answers={})
        environment = {"LAYA_CHECKPOINT_PATH": "some/checkpoint", "LAYA_DEVICE": "cpu"}
        with (
            patch.dict(environ, environment),
            patch(
                "src.infrastructure.wirings.analyze_document_use_case_wiring.load",
                return_value=fake_agent,
            ) as load,
        ):
            port = AnalyzeDocumentUseCaseWiring()._get_laya_decision_port()

        load.assert_called_once_with("some/checkpoint", device="cpu")
        self.assertIsInstance(port, LayaDecisionAdapter)
        self.assertIs(port._agent, fake_agent)
        self.assertIn("s4_intent", port._questions)

    def test_article_classifier_no_longer_depends_on_research_intent_detector(self):
        result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        self.assertFalse(hasattr(result._article_classifier, "_research_intent_detector"))

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
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.quality_threshold, 6.5)

    def test_env_var_overrides_grammar_threshold(self):
        with patch.dict(environ, {"GRAMMAR_THRESHOLD": "5.0"}):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.grammar_threshold, 5.0)

    def test_default_thresholds_when_env_vars_absent(self):
        env_without = {k: v for k, v in environ.items() if k not in self.RECOMMENDATION_ENV_VARS}
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
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
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.critical_quality_threshold, 4.0)

    def test_env_var_overrides_critical_grammar_threshold(self):
        with patch.dict(environ, {"CRITICAL_GRAMMAR_THRESHOLD": "4.0"}):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        settings: RecommendationSettingsDTO = result._recommendation_builder._settings
        self.assertAlmostEqual(settings.critical_grammar_threshold, 4.0)

    def test_env_var_overrides_structure_max_header_length(self):
        with patch.dict(environ, {"STRUCTURE_MAX_HEADER_LENGTH": "50"}):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        self.assertEqual(result._structure_validator._max_header_length, 50)

    def test_default_structure_max_header_length_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "STRUCTURE_MAX_HEADER_LENGTH"}
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        self.assertEqual(result._structure_validator._max_header_length, 100)

    def test_env_var_overrides_citation_max_author_name_length(self):
        with patch.dict(environ, {"CITATION_MAX_AUTHOR_NAME_LENGTH": "5"}):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        port = result._citation_extractor._citation_extraction_port
        self.assertEqual(port._max_author_name_length, 5)

    def test_default_citation_max_author_name_length_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "CITATION_MAX_AUTHOR_NAME_LENGTH"}
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        port = result._citation_extractor._citation_extraction_port
        self.assertEqual(port._max_author_name_length, 100)

    def test_env_var_overrides_grammar_max_replacements(self):
        with patch.dict(environ, {"GRAMMAR_MAX_REPLACEMENTS": "2"}):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        port = result._grammar_checker._grammar_check_port
        self.assertEqual(port._max_replacements, 2)

    def test_default_grammar_max_replacements_when_env_var_absent(self):
        env_without = {k: v for k, v in environ.items() if k != "GRAMMAR_MAX_REPLACEMENTS"}
        with patch.dict(environ, env_without, clear=True):
            result = AnalyzeDocumentUseCaseWiringForTest().create_use_case()
        port = result._grammar_checker._grammar_check_port
        self.assertEqual(port._max_replacements, 3)
