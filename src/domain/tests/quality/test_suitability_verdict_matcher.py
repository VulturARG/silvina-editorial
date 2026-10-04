from unittest import TestCase

from src.domain.enums.alignment_verdict import AlignmentVerdict
from src.domain.enums.contribution_verdict import ContributionVerdict
from src.domain.quality.suitability_verdict_matcher import SuitabilityVerdictMatcher


class TestSuitabilityVerdictMatcher(TestCase):
    def setUp(self) -> None:
        self.matcher = SuitabilityVerdictMatcher()

    def test_matches_contribution_not_supported(self) -> None:
        raw_text = "EL RESULTADO ES NO SUSTENTADA POR EL AUTOR"

        result = self.matcher.match(raw_text, ContributionVerdict)

        self.assertIs(result, ContributionVerdict.NOT_SUPPORTED)

    def test_contribution_not_supported_is_not_misdetected_as_supported(self) -> None:
        raw_text = "NO SUSTENTADA"

        result = self.matcher.match(raw_text, ContributionVerdict)

        self.assertIsNot(result, ContributionVerdict.SUPPORTED)
        self.assertIs(result, ContributionVerdict.NOT_SUPPORTED)

    def test_matches_contribution_partial(self) -> None:
        raw_text = "PARCIALMENTE JUSTIFICADO PERO PARCIAL"

        result = self.matcher.match(raw_text, ContributionVerdict)

        self.assertIs(result, ContributionVerdict.PARTIAL)

    def test_matches_contribution_supported(self) -> None:
        raw_text = "SUSTENTADA EN EL MARCO TEORICO"

        result = self.matcher.match(raw_text, ContributionVerdict)

        self.assertIs(result, ContributionVerdict.SUPPORTED)

    def test_contribution_defaults_to_first_declared_member_when_unmatched(self) -> None:
        raw_text = "VEREDICTO DESCONOCIDO O VACIO"

        result = self.matcher.match(raw_text, ContributionVerdict)

        first_declared = next(iter(ContributionVerdict))
        self.assertIs(result, first_declared)
        self.assertIs(result, ContributionVerdict.NOT_SUPPORTED)

    def test_matches_alignment_not_aligned(self) -> None:
        raw_text = "EL TRABAJO NO ALINEADO CON LAS LINEAS"

        result = self.matcher.match(raw_text, AlignmentVerdict)

        self.assertIs(result, AlignmentVerdict.NOT_ALIGNED)

    def test_alignment_not_aligned_is_not_misdetected_as_aligned(self) -> None:
        raw_text = "NO ALINEADO"

        result = self.matcher.match(raw_text, AlignmentVerdict)

        self.assertIsNot(result, AlignmentVerdict.ALIGNED)
        self.assertIs(result, AlignmentVerdict.NOT_ALIGNED)

    def test_matches_alignment_partially_aligned(self) -> None:
        raw_text = "SE CONSIDERA PARCIALMENTE ALINEADO"

        result = self.matcher.match(raw_text, AlignmentVerdict)

        self.assertIs(result, AlignmentVerdict.PARTIALLY_ALIGNED)

    def test_alignment_partially_aligned_is_not_misdetected_as_aligned(self) -> None:
        raw_text = "PARCIALMENTE ALINEADO"

        result = self.matcher.match(raw_text, AlignmentVerdict)

        self.assertIsNot(result, AlignmentVerdict.ALIGNED)
        self.assertIs(result, AlignmentVerdict.PARTIALLY_ALIGNED)

    def test_matches_alignment_aligned(self) -> None:
        raw_text = "TOTALMENTE ALINEADO"

        result = self.matcher.match(raw_text, AlignmentVerdict)

        self.assertIs(result, AlignmentVerdict.ALIGNED)

    def test_alignment_defaults_to_first_declared_member_when_unmatched(self) -> None:
        raw_text = "SIN VEREDICTO IDENTIFICABLE"

        result = self.matcher.match(raw_text, AlignmentVerdict)

        first_declared = next(iter(AlignmentVerdict))
        self.assertIs(result, first_declared)
        self.assertIs(result, AlignmentVerdict.NOT_ALIGNED)

    def test_repeated_and_interleaved_calls_produce_identical_results(self) -> None:
        sample_contribution = "SUSTENTADA"
        sample_alignment = "PARCIALMENTE ALINEADO"

        contribution_first = self.matcher.match(sample_contribution, ContributionVerdict)
        alignment_first = self.matcher.match(sample_alignment, AlignmentVerdict)
        contribution_second = self.matcher.match(sample_contribution, ContributionVerdict)
        alignment_second = self.matcher.match(sample_alignment, AlignmentVerdict)

        self.assertIs(contribution_first, contribution_second)
        self.assertIs(alignment_first, alignment_second)
