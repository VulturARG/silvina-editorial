from unittest import TestCase

from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.laya_text_sample_settings_dto import LayaTextSampleSettingsDTO
from src.domain.laya.laya_text_sampler import LayaTextSampler


def build_document_content(
    paragraphs: list[str], title: str | None = "Titulo"
) -> DocumentContentDTO:
    full_text = " ".join(paragraphs)
    return DocumentContentDTO(
        word_count=len(full_text.split()),
        char_count=len(full_text),
        paragraph_count=len(paragraphs),
        title=title,
        paragraphs=paragraphs,
    )


def build_sampler(
    min_sample_word_count: int = 400,
    text_sample_character_limit: int = 8000,
    reference_line_prefix_length: int = 80,
    introduction_paragraph_count: int = 3,
    middle_paragraph_count: int = 2,
    conclusion_paragraph_limit: int = 3,
    fallback_tail_paragraph_count: int = 2,
    conclusion_header_marker: str = "conclusi",
) -> LayaTextSampler:
    return LayaTextSampler(
        text_sample_settings=LayaTextSampleSettingsDTO(
            min_sample_word_count=min_sample_word_count,
            text_sample_character_limit=text_sample_character_limit,
            reference_line_prefix_length=reference_line_prefix_length,
            introduction_paragraph_count=introduction_paragraph_count,
            middle_paragraph_count=middle_paragraph_count,
            conclusion_paragraph_limit=conclusion_paragraph_limit,
            fallback_tail_paragraph_count=fallback_tail_paragraph_count,
            conclusion_header_marker=conclusion_header_marker,
        )
    )


def build_long_paragraphs() -> list[str]:
    return [
        "Intro1 " + "palabra " * 60,
        "Intro2 " + "palabra " * 60,
        "Intro3 " + "palabra " * 60,
        "Relleno4 " + "palabra " * 100,
        "Relleno5 " + "palabra " * 100,
        "Medio6 " + "palabra " * 100,
        "Medio7 " + "palabra " * 100,
        "Relleno8 " + "palabra " * 100,
        "Relleno9 " + "palabra " * 100,
        "Cierre10 " + "palabra " * 100,
    ]


class TestLayaTextSampler(TestCase):
    def test_sample_starts_with_the_title(self):
        sample = build_sampler().build_sample(build_document_content(build_long_paragraphs()))

        self.assertTrue(sample.startswith("Titulo Intro1 "))

    def test_sample_includes_introduction_middle_and_tail_paragraphs(self):
        sample = build_sampler().build_sample(build_document_content(build_long_paragraphs()))

        for included_label in ("Intro1", "Intro2", "Intro3", "Medio6", "Medio7", "Relleno9"):
            self.assertIn(included_label, sample)
        for excluded_label in ("Relleno4", "Relleno5", "Relleno8"):
            self.assertNotIn(excluded_label, sample)
        self.assertTrue(sample.rstrip().endswith("palabra"))
        self.assertIn("Cierre10", sample)

    def test_conclusion_paragraphs_replace_the_tail_when_a_conclusion_header_exists(self):
        paragraphs = build_long_paragraphs()
        paragraphs[7] = "Conclusiones " + "palabra " * 10
        sample = build_sampler().build_sample(build_document_content(paragraphs))

        self.assertIn("Conclusiones", sample)
        self.assertIn("Relleno9", sample)
        self.assertIn("Cierre10", sample)

    def test_conclusion_paragraphs_are_capped_by_the_conclusion_limit(self):
        paragraphs = build_long_paragraphs()
        paragraphs[7] = "Conclusiones " + "palabra " * 10
        sample = build_sampler(min_sample_word_count=1, conclusion_paragraph_limit=1).build_sample(
            build_document_content(paragraphs)
        )

        self.assertIn("Conclusiones", sample)
        self.assertNotIn("Relleno9", sample)

    def test_conclusion_header_marker_is_configurable_and_case_insensitive(self):
        paragraphs = build_long_paragraphs()
        paragraphs[7] = "CIERRE FINAL " + "palabra " * 10
        sample = build_sampler(
            min_sample_word_count=1,
            conclusion_header_marker="cierre final",
            conclusion_paragraph_limit=1,
        ).build_sample(build_document_content(paragraphs))

        self.assertIn("CIERRE FINAL", sample)
        self.assertNotIn("Cierre10", sample)

    def test_conclusion_paragraphs_exclude_reference_like_lines(self):
        paragraphs = build_long_paragraphs()
        paragraphs[7] = "En conclusion, el trabajo demuestra " + "palabra " * 100
        paragraphs[8] = "https://doi.org/10.1234 referencia bibliografica excluida"
        sample = build_sampler().build_sample(build_document_content(paragraphs))

        self.assertNotIn("referencia bibliografica excluida", sample)

    def test_introduction_and_middle_counts_are_configurable(self):
        sample = build_sampler(
            min_sample_word_count=1, introduction_paragraph_count=1, middle_paragraph_count=1
        ).build_sample(build_document_content(build_long_paragraphs()))

        self.assertIn("Intro1", sample)
        self.assertNotIn("Intro2", sample)
        self.assertIn("Medio6", sample)
        self.assertNotIn("Medio7", sample)

    def test_fallback_tail_paragraph_count_is_configurable(self):
        sample = build_sampler(fallback_tail_paragraph_count=1).build_sample(
            build_document_content(build_long_paragraphs())
        )

        self.assertIn("Cierre10", sample)
        self.assertNotIn("Relleno9", sample)

    def test_short_sample_falls_back_to_full_document_text(self):
        paragraphs = ["Intro corta."] * 3 + ["Parrafo de relleno."] * 2 + ["Conclusion breve."]
        sample = build_sampler().build_sample(build_document_content(paragraphs))

        self.assertEqual(sample, " ".join(paragraphs))

    def test_sample_completes_the_paragraph_crossing_the_character_limit(self):
        paragraphs = ["Corto uno.", "Corto dos.", "PARRAFO_FINAL " + "palabra " * 50]
        sample = build_sampler(
            min_sample_word_count=10000, text_sample_character_limit=25
        ).build_sample(build_document_content(paragraphs))

        self.assertEqual(sample, " ".join(paragraphs))

    def test_sample_stops_after_the_paragraph_crossing_the_character_limit(self):
        sample = build_sampler(
            min_sample_word_count=1, text_sample_character_limit=20
        ).build_sample(build_document_content(build_long_paragraphs()))

        self.assertIn("Intro1", sample)
        self.assertNotIn("Intro2", sample)

    def test_reference_line_prefix_length_limits_where_markers_are_searched(self):
        paragraphs = build_long_paragraphs()
        paragraphs[-1] = "Cierre10 texto largo antes del enlace https://ejemplo"
        sample = build_sampler(reference_line_prefix_length=10).build_sample(
            build_document_content(paragraphs)
        )

        self.assertIn("Cierre10", sample)

    def test_missing_title_contributes_an_empty_leading_part(self):
        sample = build_sampler().build_sample(
            build_document_content(build_long_paragraphs(), title=None)
        )

        self.assertTrue(sample.startswith(" Intro1 "))
