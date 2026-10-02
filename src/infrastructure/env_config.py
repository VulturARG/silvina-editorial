from os import getenv
from pathlib import Path

from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.enums.app_mode import AppMode

_VERSION_FILE_PATH = Path(__file__).resolve().parents[2] / "version.txt"


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
        self.structure_max_header_length: int = int(getenv("STRUCTURE_MAX_HEADER_LENGTH", "100"))

        self.article_classifier_temperature: float = float(
            getenv("ARTICLE_CLASSIFIER_TEMPERATURE", "0.1")
        )
        self.article_classifier_num_predict: int = int(
            getenv("ARTICLE_CLASSIFIER_NUM_PREDICT", "300")
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

        self.ollama_model_name: str = getenv(
            "OLLAMA_MODEL_NAME", "hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS"
        )
        self.ollama_base_url: str = getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_think: bool = self._parse_boolean("OLLAMA_THINK", "false")
        self.app_mode: AppMode = AppMode(getenv("APP_MODE", "PROD").strip().upper())
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
