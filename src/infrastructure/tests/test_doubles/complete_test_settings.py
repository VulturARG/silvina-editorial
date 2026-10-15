from typing import Any


class CompleteTestSettings:
    """Provides a complete settings file whose every value is distinct and recognizable."""

    _ENTRIES: tuple[tuple[str, str, str, int | float | str], ...] = (
        ("grammar", "max_replacements", "grammar_max_replacements", 211),
        ("grammar", "max_paragraphs", "grammar_max_paragraphs", 223),
        ("grammar", "max_chars", "grammar_max_chars", 4321),
        ("grammar", "max_errors", "grammar_max_errors", 239),
        ("structure", "max_header_length", "structure_max_header_length", 149),
        ("citation", "max_author_name_length", "citation_max_author_name_length", 137),
        ("article_classifier", "temperature", "article_classifier_temperature", 0.37),
        ("article_classifier", "num_predict", "article_classifier_num_predict", 421),
        ("article_size", "short_min_chars", "article_size_short_min_chars", 15017),
        ("article_size", "short_max_chars", "article_size_short_max_chars", 25019),
        ("article_size", "undefined_min_chars", "article_size_undefined_min_chars", 25021),
        ("article_size", "undefined_max_chars", "article_size_undefined_max_chars", 34023),
        ("article_size", "long_min_chars", "article_size_long_min_chars", 34029),
        ("article_size", "long_max_chars", "article_size_long_max_chars", 41031),
        ("quality_level", "excellent_threshold", "quality_level_excellent_threshold", 9.4),
        ("quality_level", "good_threshold", "quality_level_good_threshold", 7.6),
        ("quality_level", "acceptable_threshold", "quality_level_acceptable_threshold", 5.8),
        (
            "quality_level",
            "needs_improvement_threshold",
            "quality_level_needs_improvement_threshold",
            3.2,
        ),
        ("recommendation", "publish_threshold", "publish_threshold", 6.1),
        ("recommendation", "quality_threshold", "quality_threshold", 6.3),
        ("recommendation", "grammar_threshold", "grammar_threshold", 6.6),
        ("recommendation", "dimension_threshold", "dimension_threshold", 5.4),
        ("recommendation", "citation_match_threshold", "citation_match_threshold", 88.5),
        (
            "recommendation",
            "critical_citation_match_threshold",
            "critical_citation_match_threshold",
            47.5,
        ),
        ("recommendation", "citation_count_threshold", "citation_count_threshold", 61),
        (
            "recommendation",
            "classification_confidence_threshold",
            "classification_confidence_threshold",
            0.63,
        ),
        ("recommendation", "critical_quality_threshold", "critical_quality_threshold", 4.1),
        ("recommendation", "critical_grammar_threshold", "critical_grammar_threshold", 4.4),
        ("report", "score_high_threshold", "report_score_high_threshold", 8.3),
        ("report", "score_medium_threshold", "report_score_medium_threshold", 6.9),
        ("report", "words_per_page", "report_words_per_page", 331),
        ("report", "max_errors_displayed", "report_max_errors_displayed", 73),
        ("report", "context_truncation_limit", "report_context_truncation_limit", 157),
        ("report", "max_replacements", "report_max_replacements", 277),
        ("upload", "max_size_bytes", "upload_max_size_bytes", 1234567),
        ("eumic_check", "min_words_for_abstract_check", "eumic_min_words_for_abstract_check", 1313),
    )

    @classmethod
    def toml_text(cls, overrides: dict[str, int | float | str | None] | None = None) -> str:
        """Return the complete settings TOML text; an override of None omits its key."""
        value_overrides = overrides or {}
        lines: list[str] = []
        current_section = ""
        for section, key, attribute_name, default_value in cls._ENTRIES:
            if section != current_section:
                if lines:
                    lines.append("")
                lines.append(f"[{section}]")
                current_section = section
            value = value_overrides.get(attribute_name, default_value)
            if value is not None:
                lines.append(f"{key} = {cls._render(value)}")
        return "\n".join(lines) + "\n"

    @classmethod
    def expected_values(cls) -> dict[str, Any]:
        """Return the value each EnvConfig attribute must hold when the complete settings are loaded."""
        return {attribute_name: value for _, _, attribute_name, value in cls._ENTRIES}

    @staticmethod
    def _render(value: int | float | str) -> str:
        if isinstance(value, str):
            return f'"{value}"'
        return repr(value)
