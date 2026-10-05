from os import getenv
from pathlib import Path
from re import fullmatch

from src.domain.dtos.classification_text_sampling_settings_dto import (
    ClassificationTextSamplingSettingsDTO,
)
from src.domain.dtos.quality_text_sampling_settings_dto import (
    QualityTextSamplingSettingsDTO,
)
from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.app_mode import AppMode
from src.infrastructure.adapters.grammar.language_tool_settings import (
    LanguageToolSettings,
)

_VERSION_FILE_PATH = Path(__file__).resolve().parents[2] / "version.txt"
_DURATION_PATTERN = r"-?(\d+(\.\d+)?(ms|s|m|h))+"


class EnvConfig:
    """Centralized environment variable configuration.

    Parses, casts, and caches all environment variables as typed instance
    attributes at instantiation time (fail-fast on bad config).
    """

    def __init__(self) -> None:
        self.citation_max_author_name_length: int = int(
            getenv("CITATION_MAX_AUTHOR_NAME_LENGTH", "100")
        )
        self.grammar_max_replacements: int = int(getenv("GRAMMAR_MAX_REPLACEMENTS", "3"))
        self.grammar_max_paragraphs: int = int(getenv("GRAMMAR_MAX_PARAGRAPHS", "20"))
        self.grammar_max_chars: int = int(getenv("GRAMMAR_MAX_CHARS", "5000"))
        self.grammar_max_errors: int = int(getenv("GRAMMAR_MAX_ERRORS", "10"))
        self.structure_max_header_length: int = int(getenv("STRUCTURE_MAX_HEADER_LENGTH", "100"))

        self.article_classifier_temperature: float = float(
            getenv("ARTICLE_CLASSIFIER_TEMPERATURE", "0.1")
        )
        self.article_classifier_num_predict: int = int(
            getenv("ARTICLE_CLASSIFIER_NUM_PREDICT", "300")
        )
        self.article_classification_sample_introduction_character_limit: int = int(
            getenv("ARTICLE_CLASSIFICATION_SAMPLE_INTRODUCTION_CHARACTER_LIMIT", "3500")
        )
        self.article_classification_sample_conclusion_character_limit: int = int(
            getenv("ARTICLE_CLASSIFICATION_SAMPLE_CONCLUSION_CHARACTER_LIMIT", "2500")
        )
        self.article_classification_sample_fallback_character_limit: int = int(
            getenv("ARTICLE_CLASSIFICATION_SAMPLE_FALLBACK_CHARACTER_LIMIT", "6000")
        )
        self.article_classification_bibliography_header_max_length: int = int(
            getenv("ARTICLE_CLASSIFICATION_BIBLIOGRAPHY_HEADER_MAX_LENGTH", "30")
        )

        self.article_size_short_min_chars: int = int(
            getenv("ARTICLE_SIZE_SHORT_MIN_CHARS", "16000")
        )
        self.article_size_short_max_chars: int = int(
            getenv("ARTICLE_SIZE_SHORT_MAX_CHARS", "24000")
        )
        self.article_size_undefined_min_chars: int = int(
            getenv("ARTICLE_SIZE_UNDEFINED_MIN_CHARS", "24001")
        )
        self.article_size_undefined_max_chars: int = int(
            getenv("ARTICLE_SIZE_UNDEFINED_MAX_CHARS", "35999")
        )
        self.article_size_long_min_chars: int = int(getenv("ARTICLE_SIZE_LONG_MIN_CHARS", "36000"))
        self.article_size_long_max_chars: int = int(getenv("ARTICLE_SIZE_LONG_MAX_CHARS", "40000"))

        self.quality_level_excellent_threshold: float = float(
            getenv("QUALITY_LEVEL_EXCELLENT_THRESHOLD", "9.0")
        )
        self.quality_level_good_threshold: float = float(
            getenv("QUALITY_LEVEL_GOOD_THRESHOLD", "7.0")
        )
        self.quality_level_acceptable_threshold: float = float(
            getenv("QUALITY_LEVEL_ACCEPTABLE_THRESHOLD", "5.0")
        )
        self.quality_level_needs_improvement_threshold: float = float(
            getenv("QUALITY_LEVEL_NEEDS_IMPROVEMENT_THRESHOLD", "3.0")
        )
        self.quality_min_sample_word_count: int = int(
            getenv("QUALITY_MIN_SAMPLE_WORD_COUNT", "400")
        )
        self.quality_text_sample_character_limit: int = int(
            getenv("QUALITY_TEXT_SAMPLE_CHARACTER_LIMIT", "8000")
        )
        self.quality_text_sample_reference_line_prefix_length: int = int(
            getenv("QUALITY_TEXT_SAMPLE_REFERENCE_LINE_PREFIX_LENGTH", "80")
        )
        self.quality_text_sample_introduction_paragraph_count: int = int(
            getenv("QUALITY_TEXT_SAMPLE_INTRODUCTION_PARAGRAPH_COUNT", "3")
        )
        self.quality_text_sample_middle_paragraph_count: int = int(
            getenv("QUALITY_TEXT_SAMPLE_MIDDLE_PARAGRAPH_COUNT", "2")
        )
        self.quality_text_sample_conclusion_paragraph_limit: int = int(
            getenv("QUALITY_TEXT_SAMPLE_CONCLUSION_PARAGRAPH_LIMIT", "3")
        )
        self.quality_text_sample_fallback_tail_paragraph_count: int = int(
            getenv("QUALITY_TEXT_SAMPLE_FALLBACK_TAIL_PARAGRAPH_COUNT", "2")
        )
        self.quality_text_sample_conclusion_header_marker: str = getenv(
            "QUALITY_TEXT_SAMPLE_CONCLUSION_HEADER_MARKER", "conclusi"
        )

        self.ollama_model_name: str = getenv("OLLAMA_MODEL_NAME", "gemma4-26b-adapted")
        self.ollama_base_url: str = getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_think: bool = self._parse_boolean("OLLAMA_THINK", "false")
        self.ollama_model_keep_alive: str = self._parse_ollama_keep_alive()
        self.ollama_num_ctx: int | None = self._parse_ollama_num_ctx()
        self.ollama_warmup_on_startup: bool = self._parse_boolean(
            "OLLAMA_WARMUP_ON_STARTUP", "true"
        )
        self.external_llm_think: bool = self._parse_boolean("EXTERNAL_LLM_THINK", "false")
        self.app_mode: AppMode = AppMode(getenv("APP_MODE", "PROD").strip().upper())
        self.use_external_llm: bool = self._parse_boolean("USE_EXTERNAL_LLM", "false")
        self.llm_provider: AiProvider = self._parse_llm_provider(
            self.app_mode, self.use_external_llm
        )
        self.external_llm_model_name: str | None = self._parse_external_llm_model_name(
            self.app_mode, self.use_external_llm
        )
        self.metrics_database_path: str = self._get_required_env("METRICS_DATABASE_PATH")
        self.log_file_path: str = self._get_required_env("LOG_FILE_PATH")
        self.log_level: str = getenv("LOG_LEVEL", "INFO").strip().upper()
        self.log_retention_days: int = int(getenv("LOG_RETENTION_DAYS", "14"))

        # Recommendation thresholds: drive PublicationVerdictEvaluator and
        # the recommendation builder's publish/quality gating.
        self.publish_threshold: float = float(getenv("PUBLISH_THRESHOLD", "7.0"))
        self.quality_threshold: float = float(getenv("QUALITY_THRESHOLD", "7.0"))
        self.grammar_threshold: float = float(getenv("GRAMMAR_THRESHOLD", "7.0"))
        self.dimension_threshold: float = float(getenv("DIMENSION_THRESHOLD", "6.0"))
        self.citation_match_threshold: float = float(getenv("CITATION_MATCH_THRESHOLD", "90.0"))
        self.critical_citation_match_threshold: float = float(
            getenv("CRITICAL_CITATION_MATCH_THRESHOLD", "50.0")
        )
        self.citation_count_threshold: int = int(getenv("CITATION_COUNT_THRESHOLD", "10"))
        self.classification_confidence_threshold: float = float(
            getenv("CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.7")
        )
        self.critical_quality_threshold: float = float(getenv("CRITICAL_QUALITY_THRESHOLD", "5.0"))
        self.critical_grammar_threshold: float = float(getenv("CRITICAL_GRAMMAR_THRESHOLD", "5.0"))

        self.silvina_app_name: str = getenv("SILVINA_APP_NAME", "Silvina Editorial Assistant")
        self.silvina_version: str = self._resolve_version()
        self.report_score_high_threshold: float = float(
            getenv("REPORT_SCORE_HIGH_THRESHOLD", "8.0")
        )
        self.report_score_medium_threshold: float = float(
            getenv("REPORT_SCORE_MEDIUM_THRESHOLD", "6.0")
        )
        self.report_words_per_page: int = int(getenv("REPORT_WORDS_PER_PAGE", "250"))
        self.report_max_errors_displayed: int = int(getenv("REPORT_MAX_ERRORS_DISPLAYED", "5"))
        self.report_context_truncation_limit: int = int(
            getenv("REPORT_CONTEXT_TRUNCATION_LIMIT", "150")
        )
        self.report_max_replacements: int = int(getenv("REPORT_MAX_REPLACEMENTS", "3"))
        self.upload_max_size_bytes: int = int(getenv("UPLOAD_MAX_SIZE_BYTES", "26214400"))

    def get_recommendation_settings(self) -> RecommendationSettingsDTO:
        """Builds RecommendationSettingsDTO from cached configuration values."""
        return RecommendationSettingsDTO(
            publish_threshold=self.publish_threshold,
            quality_threshold=self.quality_threshold,
            grammar_threshold=self.grammar_threshold,
            dimension_threshold=self.dimension_threshold,
            citation_match_threshold=self.citation_match_threshold,
            critical_citation_match_threshold=self.critical_citation_match_threshold,
            citation_count_threshold=self.citation_count_threshold,
            classification_confidence_threshold=self.classification_confidence_threshold,
            critical_quality_threshold=self.critical_quality_threshold,
            critical_grammar_threshold=self.critical_grammar_threshold,
        )

    def get_quality_text_sampling_settings(self) -> QualityTextSamplingSettingsDTO:
        """Builds QualityTextSamplingSettingsDTO from cached configuration values."""
        return QualityTextSamplingSettingsDTO(
            min_sample_word_count=self.quality_min_sample_word_count,
            text_sample_character_limit=self.quality_text_sample_character_limit,
            reference_line_prefix_length=self.quality_text_sample_reference_line_prefix_length,
            introduction_paragraph_count=self.quality_text_sample_introduction_paragraph_count,
            middle_paragraph_count=self.quality_text_sample_middle_paragraph_count,
            conclusion_paragraph_limit=self.quality_text_sample_conclusion_paragraph_limit,
            fallback_tail_paragraph_count=self.quality_text_sample_fallback_tail_paragraph_count,
            conclusion_header_marker=self.quality_text_sample_conclusion_header_marker,
        )

    def get_classification_text_sampling_settings(
        self,
    ) -> ClassificationTextSamplingSettingsDTO:
        """Builds ClassificationTextSamplingSettingsDTO from cached configuration values."""
        return ClassificationTextSamplingSettingsDTO(
            introduction_character_limit=self.article_classification_sample_introduction_character_limit,
            conclusion_character_limit=self.article_classification_sample_conclusion_character_limit,
            fallback_character_limit=self.article_classification_sample_fallback_character_limit,
            bibliography_header_max_length=self.article_classification_bibliography_header_max_length,
        )

    def get_language_tool_settings(self) -> LanguageToolSettings:
        """Builds LanguageToolSettings from cached configuration values."""
        return LanguageToolSettings(
            max_replacements=self.grammar_max_replacements,
            max_paragraphs=self.grammar_max_paragraphs,
            max_chars=self.grammar_max_chars,
            max_errors=self.grammar_max_errors,
        )

    def _get_required_env(self, name: str) -> str:
        value = getenv(name, "").strip()
        if not value:
            raise ValueError(f"Required environment variable {name} is not set")
        return value

    def _resolve_version(self) -> str:
        """Resolves the application version.

        In testing mode (TESTING env var set to "True"/"true"/"1"), falls
        back to the SILVINA_VERSION env var (default "0.9") without
        requiring version.txt to exist. Otherwise, reads version.txt from
        the project root, letting FileNotFoundError (or other OS errors)
        propagate if the file is missing or unreadable.
        """
        if getenv("TESTING", "").lower() in ("true", "1"):
            return getenv("SILVINA_VERSION", "0.9")
        return _VERSION_FILE_PATH.read_text().strip()

    def _parse_ollama_keep_alive(self) -> str:
        raw_value = getenv("OLLAMA_MODEL_KEEP_ALIVE", "15m").strip()
        if not fullmatch(_DURATION_PATTERN, raw_value):
            raise ValueError(
                f"Invalid value for environment variable OLLAMA_MODEL_KEEP_ALIVE: '{raw_value}' "
                f"(expected a duration with a unit such as '15m', '1h' or '90s')"
            )
        return raw_value

    def _parse_ollama_num_ctx(self) -> int | None:
        raw_value = getenv("OLLAMA_NUM_CTX")
        if raw_value is None:
            return None
        trimmed_value = raw_value.strip()
        if not trimmed_value:
            return None
        try:
            parsed_value = int(trimmed_value)
            if parsed_value <= 0:
                raise ValueError
            return parsed_value
        except ValueError:
            raise ValueError(
                f"Invalid value for environment variable OLLAMA_NUM_CTX: '{trimmed_value}' "
                f"(expected a positive integer)"
            ) from None

    def _parse_boolean(self, variable_name: str, default: str) -> bool:
        """Parse an environment variable strictly as a boolean."""
        raw_value = getenv(variable_name, default).strip().lower()
        if raw_value == "true":
            return True
        if raw_value == "false":
            return False
        raise ValueError(
            f"Invalid boolean value for environment variable {variable_name}: '{raw_value}' (expected 'true' or 'false')"
        )

    def _parse_llm_provider(self, app_mode: AppMode, use_external_llm: bool) -> AiProvider:
        if app_mode is not AppMode.DEBUG or not use_external_llm:
            return AiProvider.OLLAMA

        raw_value = getenv("LLM_PROVIDER", "").strip().lower()
        if not raw_value:
            raise ValueError(
                "Environment variable LLM_PROVIDER is required when external LLM is enabled"
            )

        accepted_external_providers = {
            member.value: member for member in AiProvider if member is not AiProvider.OLLAMA
        }
        if raw_value not in accepted_external_providers:
            accepted_values = ", ".join(
                repr(member.value) for member in accepted_external_providers.values()
            )
            raise ValueError(
                f"Invalid value for environment variable LLM_PROVIDER: '{raw_value}' "
                f"(accepted values: {accepted_values})"
            )

        return accepted_external_providers[raw_value]

    def _parse_external_llm_model_name(
        self, app_mode: AppMode, use_external_llm: bool
    ) -> str | None:
        if app_mode is not AppMode.DEBUG or not use_external_llm:
            return None

        raw_value = getenv("EXTERNAL_LLM_MODEL_NAME", "").strip()
        if not raw_value:
            raise ValueError(
                "Environment variable EXTERNAL_LLM_MODEL_NAME is required when external LLM is enabled"
            )

        return raw_value
