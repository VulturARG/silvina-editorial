from unittest import TestCase

from src.domain.citation.citation_matcher import CitationMatcher
from src.domain.dtos.citation_dto import CitationDTO
from src.domain.dtos.reference_dto import ReferenceDTO
from src.domain.enums.citation_type import CitationType
from src.domain.enums.section_name import SectionName


class TestCitationMatcher(TestCase):
    def setUp(self):
        self.matcher = CitationMatcher()

    def test_s01_institutional_acronym_is_non_author(self):
        self.assertEqual(self.matcher._normalize_author("UNESCO 2020"), "__non_author__")

    def test_s02_arxiv_identifier_is_non_author(self):
        self.assertEqual(self.matcher._normalize_author("arXiv:2404.19573"), "__non_author__")

    def test_s03_doi_identifier_is_non_author(self):
        self.assertEqual(self.matcher._normalize_author("doi:10.1234/example"), "__non_author__")

    def test_s04_repositorio_prefix_is_non_author(self):
        self.assertEqual(self.matcher._normalize_author("repositorio trazable"), "__non_author__")

    def test_s05_no_hay_prefix_is_non_author(self):
        self.assertEqual(self.matcher._normalize_author("no hay dataset"), "__non_author__")

    def test_s06_multi_year_date_range_is_non_author(self):
        self.assertEqual(self.matcher._normalize_author("Datos 2018-2022"), "__non_author__")

    def test_s07_et_al_and_year_are_stripped(self):
        self.assertEqual(self.matcher._normalize_author("Wei, J. et al. (2022)"), "wei")

    def test_s08_spanish_y_conjunction_is_stripped(self):
        self.assertEqual(self.matcher._normalize_author("García y Pérez (2020)"), "garcía")

    def test_s09_single_letter_initials_are_stripped(self):
        self.assertEqual(self.matcher._normalize_author("A. Smith (2019)"), "smith")

    def test_s10_punctuation_is_stripped(self):
        self.assertEqual(self.matcher._normalize_author("Smith, J. (2019)."), "smith")

    def test_s11_long_form_date_is_stripped(self):
        self.assertEqual(self.matcher._normalize_author("Smith, J. (15 de enero de 2019)"), "smith")

    def test_s12_result_is_lowercased(self):
        self.assertEqual(self.matcher._normalize_author("SMITH (2019)"), "smith")

    def test_s13_citable_excludes_footnotes_and_authorless_citations(self):
        footnote = CitationDTO(
            text="1", citation_type=CitationType.FOOTNOTE, location=0, author="Smith"
        )
        authorless = CitationDTO(
            text="(2020)", citation_type=CitationType.AUTHOR_YEAR, location=1, author=None
        )
        valid = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=2, author="Smith"
        )
        result = self.matcher._citable([footnote, authorless, valid])
        self.assertEqual(result, [valid])

    def test_s14_build_citation_keys_uses_citable_citations_only(self):
        footnote = CitationDTO(
            text="1", citation_type=CitationType.FOOTNOTE, location=0, author="Smith"
        )
        valid = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=1, author="Smith"
        )
        result = self.matcher._build_citation_keys([footnote, valid])
        self.assertEqual(result, {"smith": valid})

    def test_s15_build_reference_keys_uses_all_references(self):
        reference = ReferenceDTO(text="Smith, J. (2020). Title.")
        result = self.matcher._build_reference_keys([reference])
        self.assertEqual(result, {"smith": reference})

    def test_s16_non_author_citation_is_never_orphaned(self):
        citation = CitationDTO(
            text="(UNESCO, 2020)",
            citation_type=CitationType.AUTHOR_YEAR,
            location=0,
            author="UNESCO 2020",
        )
        self.assertFalse(self.matcher._is_orphaned_citation(citation, {}))

    def test_s17_citation_absent_from_reference_keys_is_orphaned(self):
        citation = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        self.assertTrue(self.matcher._is_orphaned_citation(citation, {}))

    def test_s18_citation_present_in_reference_keys_is_not_orphaned(self):
        citation = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        reference = ReferenceDTO(text="Smith, J. (2020). Title.")
        self.assertFalse(self.matcher._is_orphaned_citation(citation, {"smith": reference}))

    def test_s19_empty_citations_and_references_yield_no_orphaned_citations(self):
        self.assertEqual(self.matcher.find_orphaned_citations([], []), [])

    def test_s20_all_citations_matched_yields_no_orphaned_citations(self):
        citation = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        reference = ReferenceDTO(text="Smith, J. (2020). Title.")
        self.assertEqual(self.matcher.find_orphaned_citations([citation], [reference]), [])

    def test_s21_unmatched_citation_is_returned_as_orphaned(self):
        matched = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        unmatched = CitationDTO(
            text="(Jones, 2021)", citation_type=CitationType.AUTHOR_YEAR, location=1, author="Jones"
        )
        reference = ReferenceDTO(text="Smith, J. (2020). Title.")
        result = self.matcher.find_orphaned_citations([matched, unmatched], [reference])
        self.assertEqual(result, [unmatched])

    def test_s22_footnote_citations_are_excluded_even_when_unmatched(self):
        footnote = CitationDTO(
            text="1", citation_type=CitationType.FOOTNOTE, location=0, author="Jones"
        )
        self.assertEqual(self.matcher.find_orphaned_citations([footnote], []), [])

    def test_s23_all_references_cited_yields_no_orphaned_references(self):
        citation = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        reference = ReferenceDTO(text="Smith, J. (2020). Title.")
        self.assertEqual(self.matcher.find_orphaned_references([citation], [reference]), [])

    def test_s24_uncited_reference_is_returned_as_orphaned(self):
        citation = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        cited_reference = ReferenceDTO(text="Smith, J. (2020). Title.")
        uncited_reference = ReferenceDTO(text="Jones, A. (2021). Other.")
        result = self.matcher.find_orphaned_references(
            [citation], [cited_reference, uncited_reference]
        )
        self.assertEqual(result, [uncited_reference])

    def test_s25_empty_inputs_yield_zeroed_result(self):
        result = self.matcher.match_citations_to_references(
            [], [], section_type=SectionName.REFERENCES
        )
        self.assertEqual(result.total_citations, 0)
        self.assertEqual(result.matched_count, 0)
        self.assertEqual(result.unmatched_count, 0)
        self.assertEqual(result.unmatched_citations, [])

    def test_s26_all_citations_matched_counts_correctly(self):
        citations = [
            CitationDTO(
                text=f"(Author{i}, 2020)",
                citation_type=CitationType.AUTHOR_YEAR,
                location=i,
                author=f"Author{i}",
            )
            for i in range(3)
        ]
        references = [ReferenceDTO(text=f"Author{i}, X. (2020). Title.") for i in range(3)]
        result = self.matcher.match_citations_to_references(citations, references)
        self.assertEqual(result.matched_count, 3)
        self.assertEqual(result.unmatched_count, 0)

    def test_s27_some_citations_orphaned(self):
        matched = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        unmatched = CitationDTO(
            text="(Jones, 2021)", citation_type=CitationType.AUTHOR_YEAR, location=1, author="Jones"
        )
        reference = ReferenceDTO(text="Smith, J. (2020). Title.")
        result = self.matcher.match_citations_to_references([matched, unmatched], [reference])
        self.assertEqual(result.matched_count, 1)
        self.assertEqual(result.unmatched_count, 1)
        self.assertEqual(result.unmatched_citations, [unmatched.text])

    def test_s28_footnote_citations_excluded_from_total_citations(self):
        authored = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        footnote = CitationDTO(
            text="1", citation_type=CitationType.FOOTNOTE, location=1, author="Smith"
        )
        result = self.matcher.match_citations_to_references([authored, footnote], [])
        self.assertEqual(result.total_citations, 1)

    def test_s29_section_type_accepts_enum_member(self):
        result = self.matcher.match_citations_to_references(
            [], [], section_type=SectionName.REFERENCES
        )
        self.assertEqual(result.total_citations, 0)

    def test_s30_repeated_calls_do_not_share_state_between_calls(self):
        first_citation = CitationDTO(
            text="(Jones, 2021)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Jones"
        )
        first_result = self.matcher.find_orphaned_citations([first_citation], [])
        self.assertEqual(first_result, [first_citation])

        second_citation = CitationDTO(
            text="(Smith, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="Smith"
        )
        second_reference = ReferenceDTO(text="Smith, J. (2020). Title.")
        second_result = self.matcher.find_orphaned_citations([second_citation], [second_reference])
        self.assertEqual(second_result, [])

    def test_s31_citation_with_acronym_declared_in_reference_author_part_is_not_orphaned(self):
        citation = CitationDTO(
            text="(SMRA, 2021)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="SMRA"
        )
        reference = ReferenceDTO(
            text=(
                "SECRETARÍA DE MINERÍA DE LA REPÚBLICA ARGENTINA (SMRA) (2021). "
                "Informe Litio. Octubre 2021. Recuperado de: https://example.gob.ar/litio"
            )
        )
        self.assertEqual(self.matcher.find_orphaned_citations([citation], [reference]), [])

    def test_s32_reference_with_acronym_declared_in_author_part_is_cited_by_acronym(self):
        citation = CitationDTO(
            text="(SMRA, 2021)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="SMRA"
        )
        reference = ReferenceDTO(
            text=(
                "SECRETARÍA DE MINERÍA DE LA REPÚBLICA ARGENTINA (SMRA) (2021). "
                "Informe Litio. Octubre 2021. Recuperado de: https://example.gob.ar/litio"
            )
        )
        self.assertEqual(self.matcher.find_orphaned_references([citation], [reference]), [])

    def test_s33_citation_with_acronym_no_reference_declares_stays_orphaned(self):
        citation = CitationDTO(
            text="(OMS, 2021)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="OMS"
        )
        reference = ReferenceDTO(
            text=(
                "SECRETARÍA DE MINERÍA DE LA REPÚBLICA ARGENTINA (SMRA) (2021). "
                "Informe Litio. Octubre 2021. Recuperado de: https://example.gob.ar/litio"
            )
        )
        self.assertEqual(self.matcher.find_orphaned_citations([citation], [reference]), [citation])

    def test_s34_acronym_outside_reference_author_part_is_not_declared(self):
        citation = CitationDTO(
            text="(SMRA, 2020)", citation_type=CitationType.AUTHOR_YEAR, location=0, author="SMRA"
        )
        reference = ReferenceDTO(text="Smith, J. (2020). Informe (SMRA).")
        self.assertEqual(self.matcher.find_orphaned_citations([citation], [reference]), [citation])
