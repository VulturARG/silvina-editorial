from unittest import TestCase

from src.domain.enums.apa_error_type import ApaErrorType
from src.domain.citation.apa_validator import ApaValidator
from src.domain.dtos.citation_dto import CitationDTO
from src.domain.dtos.reference_dto import ReferenceDTO
from src.domain.enums.citation_type import CitationType


class TestApaValidatorParenthetical(TestCase):
    def setUp(self):
        self.validator = ApaValidator()

    def test_s01_valid_citation_no_violations(self):
        violations = self.validator.validate_citation("(García, 2020)", 0)
        self.assertEqual(violations, [])

    def test_s02_conjunction_error_ampersand(self):
        violations = self.validator.validate_citation("(García & Pérez, 2020)", 1)
        error_types = [v.error_type for v in violations]
        self.assertIn(ApaErrorType.CONJUNCTION_ERROR, error_types)
        correction = next(
            v.correction for v in violations if v.error_type == ApaErrorType.CONJUNCTION_ERROR
        )
        self.assertIn(" y ", correction)

    def test_s03_comma_error_missing_comma(self):
        violations = self.validator.validate_citation("(García 2020)", 2)
        error_types = [v.error_type for v in violations]
        self.assertIn(ApaErrorType.COMMA_ERROR, error_types)
        correction = next(
            v.correction for v in violations if v.error_type == ApaErrorType.COMMA_ERROR
        )
        self.assertEqual(correction, "(García, 2020)")

    def test_s04_capitalization_error_lowercase_author(self):
        violations = self.validator.validate_citation("(garcía, 2020)", 3)
        error_types = [v.error_type for v in violations]
        self.assertIn(ApaErrorType.CAPITALIZATION_ERROR, error_types)

    def test_s05_et_al_format_error_extra_period(self):
        violations = self.validator.validate_citation("(García et. al., 2020)", 4)
        error_types = [v.error_type for v in violations]
        self.assertIn(ApaErrorType.ET_AL_FORMAT_ERROR, error_types)

    def test_s05b_et_al_format_error_missing_trailing_period(self):
        violations = self.validator.validate_citation("(García et al, 2020)", 5)
        error_types = [v.error_type for v in violations]
        self.assertIn(ApaErrorType.ET_AL_FORMAT_ERROR, error_types)

    def test_s06_page_format_error(self):
        violations = self.validator.validate_citation("(García, 2020, pág. 5)", 6)
        error_types = [v.error_type for v in violations]
        self.assertIn(ApaErrorType.PAGE_FORMAT_ERROR, error_types)
        correction = next(
            v.correction for v in violations if v.error_type == ApaErrorType.PAGE_FORMAT_ERROR
        )
        self.assertIn("p.", correction)

    def test_s07_spacing_error_double_space(self):
        violations = self.validator.validate_citation("(García,  2020)", 7)
        error_types = [v.error_type for v in violations]
        self.assertIn(ApaErrorType.SPACING_ERROR, error_types)

    def test_corporate_author_listed_in_references_keeps_ampersand(self):
        citation = CitationDTO(
            text="(McKinsey & Company, 2021)", citation_type=CitationType.AUTHOR_YEAR, location=0
        )
        reference = ReferenceDTO(text="McKinsey & Company. (2021). The top trends in 2021.")

        violations = self.validator.validate_all_citations(
            citations=[citation], paragraphs=["Paragraph"], references=[reference]
        )

        self.assertEqual(violations, [])

    def test_person_with_ampersand_is_still_flagged_when_references_are_given(self):
        citation = CitationDTO(
            text="(Hines & Bishop, 2013)", citation_type=CitationType.AUTHOR_YEAR, location=0
        )
        reference = ReferenceDTO(text="Hines, A., & Bishop, P. (2013). Title of the work.")

        violations = self.validator.validate_all_citations(
            citations=[citation], paragraphs=["Paragraph"], references=[reference]
        )

        error_types = [v.error_type for v in violations]
        self.assertIn(ApaErrorType.CONJUNCTION_ERROR, error_types)
