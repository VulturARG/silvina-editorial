from src.domain.quality.alignment_lines_extractor import AlignmentLinesExtractor
from src.domain.quality.contribution_observation_builder import ContributionObservationBuilder
from src.domain.quality.editorial_suitability_parser import EditorialSuitabilityParser
from src.domain.quality.first_sentence_extractor import FirstSentenceExtractor
from src.domain.quality.suitability_field_extractor import SuitabilityFieldExtractor
from src.domain.quality.suitability_field_truncator import SuitabilityFieldTruncator
from src.domain.quality.suitability_verdict_matcher import SuitabilityVerdictMatcher


class EditorialSuitabilityParserBuilderForTest:
    def build(
        self,
        phrase_max_length: int = 120,
        justification_max_length: int = 120,
        lines_max_length: int = 200,
        observation_max_length: int = 120,
        field_extractor: SuitabilityFieldExtractor | None = None,
        verdict_matcher: SuitabilityVerdictMatcher | None = None,
        lines_extractor: AlignmentLinesExtractor | None = None,
        first_sentence_extractor: FirstSentenceExtractor | None = None,
        field_truncator: SuitabilityFieldTruncator | None = None,
        observation_builder: ContributionObservationBuilder | None = None,
    ) -> EditorialSuitabilityParser:
        resolved_field_extractor = (
            field_extractor if field_extractor is not None else SuitabilityFieldExtractor()
        )
        resolved_verdict_matcher = (
            verdict_matcher if verdict_matcher is not None else SuitabilityVerdictMatcher()
        )
        resolved_lines_extractor = (
            lines_extractor
            if lines_extractor is not None
            else AlignmentLinesExtractor(field_extractor=resolved_field_extractor)
        )
        resolved_first_sentence_extractor = (
            first_sentence_extractor
            if first_sentence_extractor is not None
            else FirstSentenceExtractor()
        )
        resolved_field_truncator = (
            field_truncator
            if field_truncator is not None
            else SuitabilityFieldTruncator(
                first_sentence_extractor=resolved_first_sentence_extractor
            )
        )
        resolved_observation_builder = (
            observation_builder
            if observation_builder is not None
            else ContributionObservationBuilder(
                field_truncator=resolved_field_truncator,
                max_length=observation_max_length,
            )
        )
        return EditorialSuitabilityParser(
            field_extractor=resolved_field_extractor,
            verdict_matcher=resolved_verdict_matcher,
            lines_extractor=resolved_lines_extractor,
            field_truncator=resolved_field_truncator,
            observation_builder=resolved_observation_builder,
            phrase_max_length=phrase_max_length,
            justification_max_length=justification_max_length,
            lines_max_length=lines_max_length,
        )
