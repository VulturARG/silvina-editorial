from src.domain.dtos.alignment_assessment_dto import AlignmentAssessmentDTO
from src.domain.dtos.contribution_assessment_dto import ContributionAssessmentDTO
from src.domain.enums.alignment_verdict import AlignmentVerdict
from src.domain.enums.contribution_verdict import ContributionVerdict
from src.domain.quality.alignment_lines_extractor import AlignmentLinesExtractor
from src.domain.quality.contribution_observation_builder import ContributionObservationBuilder
from src.domain.quality.suitability_field_extractor import SuitabilityFieldExtractor
from src.domain.quality.suitability_field_truncator import SuitabilityFieldTruncator
from src.domain.quality.suitability_verdict_matcher import SuitabilityVerdictMatcher


class EditorialSuitabilityParser:
    """Orchestrates parsing of editorial suitability contribution and alignment assessments."""

    def __init__(
        self,
        field_extractor: SuitabilityFieldExtractor,
        verdict_matcher: SuitabilityVerdictMatcher,
        lines_extractor: AlignmentLinesExtractor,
        field_truncator: SuitabilityFieldTruncator,
        observation_builder: ContributionObservationBuilder,
        phrase_max_length: int,
        justification_max_length: int,
        lines_max_length: int,
    ) -> None:
        self._field_extractor = field_extractor
        self._verdict_matcher = verdict_matcher
        self._lines_extractor = lines_extractor
        self._field_truncator = field_truncator
        self._observation_builder = observation_builder
        self._phrase_max_length = phrase_max_length
        self._justification_max_length = justification_max_length
        self._lines_max_length = lines_max_length

    def parse_contribution(self, text: str) -> ContributionAssessmentDTO:
        """Parse text and return a structured contribution assessment."""
        raw_verdict_text = self._field_extractor.extract_verdict_text(text)
        verdict = self._verdict_matcher.match(raw_verdict_text, ContributionVerdict)
        raw_phrase = self._field_extractor.extract_contribution_phrase(text)
        phrase = self._field_truncator.truncate(raw_phrase, self._phrase_max_length)
        observation = self._observation_builder.build_observation(verdict, phrase)
        return ContributionAssessmentDTO(
            verdict=verdict,
            phrase=phrase,
            observation=observation,
        )

    def parse_alignment(self, text: str) -> AlignmentAssessmentDTO:
        """Parse text and return a structured alignment assessment."""
        raw_verdict_text = self._field_extractor.extract_verdict_text(text)
        verdict = self._verdict_matcher.match(raw_verdict_text, AlignmentVerdict)
        raw_lines = self._lines_extractor.extract(text)
        lines = self._field_truncator.truncate(raw_lines, self._lines_max_length)
        raw_justification = self._field_extractor.extract_justification(text)
        justification = self._field_truncator.truncate(
            raw_justification, self._justification_max_length
        )
        return AlignmentAssessmentDTO(
            verdict=verdict,
            lines=lines,
            justification=justification,
        )
