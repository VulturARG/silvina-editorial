from typing import Any
from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.quality_text_sampling_settings_dto import (
    QualityTextSamplingSettingsDTO,
)
from src.domain.quality.quality_text_sampler import QualityTextSampler


class TestQualityTextSampler(TestCase):
    def _build_document_content(
        self, paragraphs: list[str], title: str | None = "Title"
    ) -> DocumentContentDTO:
        full_text = " ".join(paragraphs)
        return DocumentContentDTO(
            word_count=len(full_text.split()),
            char_count=len(full_text),
            paragraph_count=len(paragraphs),
            title=title,
            paragraphs=paragraphs,
        )

    def _build_sampler(
        self,
        min_sample_word_count: int = 400,
        text_sample_character_limit: int = 8000,
        reference_line_prefix_length: int = 80,
        introduction_paragraph_count: int = 3,
        middle_paragraph_count: int = 2,
        conclusion_paragraph_limit: int = 3,
        fallback_tail_paragraph_count: int = 2,
        conclusion_header_marker: str = "conclusi",
    ) -> QualityTextSampler:
        quality_text_sampling_settings = QualityTextSamplingSettingsDTO(
            min_sample_word_count=min_sample_word_count,
            text_sample_character_limit=text_sample_character_limit,
            reference_line_prefix_length=reference_line_prefix_length,
            introduction_paragraph_count=introduction_paragraph_count,
            middle_paragraph_count=middle_paragraph_count,
            conclusion_paragraph_limit=conclusion_paragraph_limit,
            fallback_tail_paragraph_count=fallback_tail_paragraph_count,
            conclusion_header_marker=conclusion_header_marker,
        )
        return QualityTextSampler(quality_text_sampling_settings=quality_text_sampling_settings)

    def test_constructor_requires_settings_object_raising_type_error_when_missing(self):
        kwargs: dict[str, Any] = {}
        with self.assertRaises(TypeError):
            QualityTextSampler(**kwargs)

    def test_short_document_uses_full_text_fallback_instead_of_sample(self):
        paragraphs = ["Intro corta."] * 3 + ["Parrafo de relleno."] * 2 + ["Conclusion breve."]
        document_content = self._build_document_content(paragraphs)
        sampler = self._build_sampler()

        sample = sampler.build_sample(document_content)

        full_text = " ".join(paragraphs)
        self.assertIn(full_text[:200], sample)

    def test_long_document_uses_strategic_sample_not_full_text(self):
        excluded_paragraph = "PARRAFO_EXCLUIDO_UNICO " + ("relleno " * 10)
        paragraphs = (
            [
                "Intro uno " + "palabra " * 60,
                "Intro dos " + "palabra " * 60,
                "Intro tres " + "palabra " * 60,
            ]
            + [excluded_paragraph]
            + ["Relleno extra uno " + "palabra " * 100]
            + ["Relleno extra dos " + "palabra " * 100]
            + ["Relleno medio uno " + "palabra " * 100]
            + ["Relleno medio dos " + "palabra " * 100]
            + ["Relleno extra tres " + "palabra " * 100]
            + ["Conclusion final " + "palabra " * 100]
        )
        document_content = self._build_document_content(paragraphs)
        sampler = self._build_sampler()

        sample = sampler.build_sample(document_content)

        self.assertNotIn("PARRAFO_EXCLUIDO_UNICO", sample)

    def test_conclusion_paragraphs_exclude_reference_like_lines(self):
        paragraphs = (
            ["Intro uno.", "Intro dos.", "Intro tres."]
            + ["Relleno extra uno " + "palabra " * 100]
            + ["Relleno medio uno " + "palabra " * 100]
            + ["Relleno medio dos " + "palabra " * 100]
            + ["Relleno extra dos " + "palabra " * 100]
            + ["En conclusion, el trabajo demuestra " + "palabra " * 100]
            + ["https://doi.org/10.1234 referencia bibliografica excluida " + "palabra " * 100]
            + ["Conclusion final reafirmada " + "palabra " * 100]
        )
        document_content = self._build_document_content(paragraphs)
        sampler = self._build_sampler()

        sample = sampler.build_sample(document_content)

        self.assertNotIn("referencia bibliografica excluida", sample)

    def test_constructor_parameters_override_legacy_defaults(self):
        paragraphs = ["Palabra " * 20] * 10
        document_content = self._build_document_content(paragraphs)
        sampler = self._build_sampler(min_sample_word_count=10, text_sample_character_limit=500)

        sample = sampler.build_sample(document_content)

        self.assertGreaterEqual(len(sample), 500)
        self.assertTrue(sample.rstrip().endswith("Palabra"))

    def test_sample_completes_the_paragraph_crossing_the_limit_instead_of_cutting_mid_word(self):
        paragraphs = ["Corto uno.", "Corto dos.", "PARRAFO_FINAL " + "palabra " * 50]
        document_content = self._build_document_content(paragraphs)
        sampler = self._build_sampler(min_sample_word_count=10000, text_sample_character_limit=25)

        sample = sampler.build_sample(document_content)

        self.assertIn("PARRAFO_FINAL", sample)
        self.assertTrue(sample.rstrip().endswith("palabra"))

    def test_defaults_match_legacy_hardcoded_constants(self):
        paragraphs = ["Intro corta."] * 3 + ["Parrafo de relleno."] * 2 + ["Conclusion breve."]
        document_content = self._build_document_content(paragraphs)
        sampler = self._build_sampler()

        sample = sampler.build_sample(document_content)

        full_text = " ".join(paragraphs)
        self.assertEqual(sample, full_text[:8000])

    def test_custom_conclusion_header_marker_detects_conclusion_section(self):
        paragraphs = (
            ["Intro uno.", "Intro dos.", "Intro tres."]
            + ["Relleno medio uno " + "palabra " * 100]
            + ["Relleno medio dos " + "palabra " * 100]
            + ["En cierre final, el analisis culmina " + "palabra " * 100]
        )
        document_content = self._build_document_content(paragraphs)
        sampler = self._build_sampler(conclusion_header_marker="cierre")

        sample = sampler.build_sample(document_content)

        self.assertIn("En cierre final", sample)
