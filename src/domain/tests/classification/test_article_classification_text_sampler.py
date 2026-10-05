from typing import Any
from unittest import TestCase

from src.domain.classification.article_classification_text_sampler import (
    ArticleClassificationTextSampler,
)
from src.domain.dtos.classification_text_sampling_settings_dto import (
    ClassificationTextSamplingSettingsDTO,
)
from src.domain.dtos.document_content_dto import DocumentContentDTO


class TestArticleClassificationTextSampler(TestCase):
    def _build_document_content(self, paragraphs: list[str]) -> DocumentContentDTO:
        full_text = " ".join(paragraphs)
        return DocumentContentDTO(
            word_count=len(full_text.split()),
            char_count=len(full_text),
            paragraphs=paragraphs,
        )

    def _build_sampler(
        self,
        introduction_character_limit: int = 3500,
        conclusion_character_limit: int = 2500,
        fallback_character_limit: int = 6000,
        bibliography_header_max_length: int = 30,
    ) -> ArticleClassificationTextSampler:
        classification_text_sampling_settings = ClassificationTextSamplingSettingsDTO(
            introduction_character_limit=introduction_character_limit,
            conclusion_character_limit=conclusion_character_limit,
            fallback_character_limit=fallback_character_limit,
            bibliography_header_max_length=bibliography_header_max_length,
        )
        return ArticleClassificationTextSampler(
            classification_text_sampling_settings=classification_text_sampling_settings
        )

    def test_constructor_requires_settings_object_raising_type_error_when_missing(self):
        kwargs: dict[str, Any] = {}
        with self.assertRaises(TypeError):
            ArticleClassificationTextSampler(**kwargs)

    def test_bibliography_section_is_excluded_from_the_sample(self):
        paragraphs = (
            ["Intro uno " + "palabra " * 600]
            + ["Referencias"]
            + ["Smith 2020 entrada bibliografica excluida " + "palabra " * 100]
        )
        document_content = self._build_document_content(paragraphs)
        sampler = self._build_sampler()

        sample = sampler.build_sample(document_content)

        self.assertNotIn("entrada bibliografica excluida", sample)

    def test_sample_combines_intro_and_ending_segments(self):
        paragraphs = ["Intro " + "palabra " * 1500] + ["Final " + "palabra " * 700]
        document_content = self._build_document_content(paragraphs)
        full_text = " ".join(paragraphs)
        sampler = self._build_sampler()

        sample = sampler.build_sample(document_content)

        self.assertEqual(sample, (full_text[:3500] + " " + full_text[-2500:]).strip())

    def test_empty_sample_falls_back_to_first_six_thousand_characters_of_full_text(self):
        paragraphs = ["", "Referencias", "Entrada bibliografica " + "palabra " * 600]
        document_content = self._build_document_content(paragraphs)
        full_text = " ".join(paragraphs)
        sampler = self._build_sampler()

        sample = sampler.build_sample(document_content)

        self.assertEqual(sample, full_text[:6000])

    def test_custom_character_limits_and_header_max_length_override_defaults(self):
        paragraphs = ["Intro " + "palabra " * 100] + ["Final " + "palabra " * 100]
        document_content = self._build_document_content(paragraphs)
        full_text = " ".join(paragraphs)
        sampler = self._build_sampler(
            introduction_character_limit=100,
            conclusion_character_limit=50,
            fallback_character_limit=200,
            bibliography_header_max_length=15,
        )

        sample = sampler.build_sample(document_content)

        self.assertEqual(sample, (full_text[:100] + " " + full_text[-50:]).strip())
