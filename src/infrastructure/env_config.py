from os import getenv
from pathlib import Path

from src.domain.dtos.laya_text_sample_settings_dto import LayaTextSampleSettingsDTO
from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO

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

        self.laya_checkpoint_path: str = getenv(
            "LAYA_CHECKPOINT_PATH", "data/laya/checkpoints/laya_finetuned_v1_16epochs"
        )
        self.laya_device: str | None = getenv("LAYA_DEVICE") or None

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

        self.laya_text_sample_min_word_count: int = int(
            getenv("LAYA_TEXT_SAMPLE_MIN_WORD_COUNT", "400")
        )
        self.laya_text_sample_character_limit: int = int(
            getenv("LAYA_TEXT_SAMPLE_CHARACTER_LIMIT", "8000")
        )
        self.laya_text_sample_reference_line_prefix_length: int = int(
            getenv("LAYA_TEXT_SAMPLE_REFERENCE_LINE_PREFIX_LENGTH", "80")
        )
        self.laya_text_sample_introduction_paragraph_count: int = int(
            getenv("LAYA_TEXT_SAMPLE_INTRODUCTION_PARAGRAPH_COUNT", "3")
        )
        self.laya_text_sample_middle_paragraph_count: int = int(
            getenv("LAYA_TEXT_SAMPLE_MIDDLE_PARAGRAPH_COUNT", "2")
        )
        self.laya_text_sample_conclusion_paragraph_limit: int = int(
            getenv("LAYA_TEXT_SAMPLE_CONCLUSION_PARAGRAPH_LIMIT", "3")
        )
        self.laya_text_sample_fallback_tail_paragraph_count: int = int(
            getenv("LAYA_TEXT_SAMPLE_FALLBACK_TAIL_PARAGRAPH_COUNT", "2")
        )
        self.laya_text_sample_conclusion_header_marker: str = getenv(
            "LAYA_TEXT_SAMPLE_CONCLUSION_HEADER_MARKER", "conclusi"
        )

        self.ollama_model_name: str = getenv(
            "OLLAMA_MODEL_NAME", "hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS"
        )
        self.ollama_base_url: str = getenv("OLLAMA_BASE_URL", "http://localhost:11434")

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

    def get_laya_text_sample_settings(self) -> LayaTextSampleSettingsDTO:
        """Builds LayaTextSampleSettingsDTO from cached configuration values."""
        return LayaTextSampleSettingsDTO(
            min_sample_word_count=self.laya_text_sample_min_word_count,
            text_sample_character_limit=self.laya_text_sample_character_limit,
            reference_line_prefix_length=self.laya_text_sample_reference_line_prefix_length,
            introduction_paragraph_count=self.laya_text_sample_introduction_paragraph_count,
            middle_paragraph_count=self.laya_text_sample_middle_paragraph_count,
            conclusion_paragraph_limit=self.laya_text_sample_conclusion_paragraph_limit,
            fallback_tail_paragraph_count=self.laya_text_sample_fallback_tail_paragraph_count,
            conclusion_header_marker=self.laya_text_sample_conclusion_header_marker,
        )

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
