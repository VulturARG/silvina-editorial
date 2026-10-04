from re import DOTALL, IGNORECASE, compile

from src.domain.dtos.dimension_feedback_dto import DimensionFeedbackDTO
from src.domain.dtos.dimension_score_dto import DimensionScoreDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.quality.feedback_structure_parser import FeedbackStructureParser

_MINIMUM_FEEDBACK_LENGTH = 10
_RECOMMENDATION_TAIL_PATTERN = compile(r"\*\*RECOMENDACIÓN.*", DOTALL | IGNORECASE)
_DIMENSION_HEADING_LEVEL_PATTERN = compile(r"^(#{1,6})\s*")


class DimensionFeedbackExtractor:
    """Extracts and formats feedback text and blocks from dimension blocks."""

    def __init__(
        self,
        feedback_structure_parser: FeedbackStructureParser,
        unscored_dimension: DimensionScoreDTO,
    ) -> None:
        self._feedback_structure_parser = feedback_structure_parser
        self._unscored_dimension = unscored_dimension

    def extract(self, block: str) -> DimensionFeedbackDTO:
        """Extract feedback text and structured blocks from a dimension text block."""
        cleaned_block = _RECOMMENDATION_TAIL_PATTERN.sub("", block).strip()
        lines = cleaned_block.split("\n")
        header_line = lines[0].strip()
        heading_match = _DIMENSION_HEADING_LEVEL_PATTERN.match(header_line)
        dimension_heading_level = len(heading_match.group(1)) if heading_match is not None else 0

        blocks = self._feedback_structure_parser.parse(
            lines=lines[1:], dimension_heading_level=dimension_heading_level
        )
        feedback = self._format_feedback(blocks)
        if len(feedback) < _MINIMUM_FEEDBACK_LENGTH:
            return DimensionFeedbackDTO(feedback=self._unscored_dimension.feedback, blocks=())

        return DimensionFeedbackDTO(feedback=feedback, blocks=blocks)

    def _format_feedback(self, blocks: tuple[FeedbackBlockDTO, ...]) -> str:
        parts = [
            f"{block.text}:" if block.kind == FeedbackBlockKind.TITLE else block.text
            for block in blocks
        ]
        return " ".join(parts)
