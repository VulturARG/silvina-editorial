from src.domain.quality.feedback_line_classifier import FeedbackLineClassifier
from src.domain.quality.feedback_section_capper import FeedbackSectionCapper
from src.domain.quality.feedback_structure_parser import FeedbackStructureParser
from src.domain.quality.feedback_text_cleaner import FeedbackTextCleaner


class FeedbackStructureParserBuilderForTest:
    def build(
        self,
        maximum_items_per_section: int = 8,
        parser_class: type[FeedbackStructureParser] = FeedbackStructureParser,
    ) -> FeedbackStructureParser:
        capper = FeedbackSectionCapper(maximum_items_per_section=maximum_items_per_section)
        classifier = FeedbackLineClassifier()
        text_cleaner = FeedbackTextCleaner()
        return parser_class(
            classifier=classifier,
            capper=capper,
            text_cleaner=text_cleaner,
        )
