from re import DOTALL, IGNORECASE, compile

from src.domain.dtos.dimension_score_dto import DimensionScoreDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.dtos.parsed_response_dto import ParsedResponseDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.enums.quality_dimension import QualityDimension
from src.domain.quality.feedback_structure_parser import FeedbackStructureParser

_DIMENSION_HEADER_PATTERN = compile(
    r"(?m)(?=^[ \t]*(?:#{1,6}[ \t]+)?\*\*(?:\d+\.\s*)?(?:Claridad|Coherencia|Argumentaci[oó]n|Conclusiones))",
    IGNORECASE,
)
_EXPLICIT_SCORE_PATTERN = compile(
    r"\[Puntuaci[oó]n:\s*(\d+(?:\.\d+)?)(?:/10)?\]|(\d+(?:\.\d+)?)\s*/\s*10",
    IGNORECASE,
)
_RECOMMENDATION_TAIL_PATTERN = compile(r"\*\*RECOMENDACIÓN.*", DOTALL | IGNORECASE)
_DIMENSION_HEADING_LEVEL_PATTERN = compile(r"^(#{1,6})\s*")
_NARRATIVE_SCORE_KEYWORDS = (
    (("excelente", "sobresaliente", "muy bueno"), 8.5),
    (("bueno", "adecuado", "correcto"), 7.5),
    (("aceptable", "suficiente", "regular"), 6.0),
    (("deficiente", "débil", "pobre", "insuficiente"), 4.0),
)
_DIMENSION_KEYWORDS: tuple[tuple[QualityDimension, tuple[str, ...]], ...] = (
    (QualityDimension.ARGUMENTATION, ("argumentaci",)),
    (QualityDimension.CONCLUSIONS, ("conclusi",)),
    (QualityDimension.COHERENCE, ("coherencia",)),
    (QualityDimension.CLARITY, ("claridad", "argumento")),
)


class QualityResponseParser:
    """Parses one LLM response into per-dimension scores and feedback."""

    def __init__(
        self,
        unscored_dimension_score: float = 7.0,
        unscored_dimension_feedback: str = "No disponible",
        feedback_structure_parser: FeedbackStructureParser | None = None,
    ) -> None:
        self._unscored_dimension_score = unscored_dimension_score
        self._unscored_dimension_feedback = unscored_dimension_feedback
        self._feedback_structure_parser = feedback_structure_parser or FeedbackStructureParser()

    def parse(self, text: str) -> ParsedResponseDTO:
        """Parse an LLM response into a ParsedResponseDTO of per-dimension scores."""
        scores = {
            dimension: DimensionScoreDTO(
                self._unscored_dimension_score,
                self._unscored_dimension_feedback,
                (),
            )
            for dimension in QualityDimension
        }
        matched_dimensions: set[QualityDimension] = set()

        blocks = _DIMENSION_HEADER_PATTERN.split(text.strip())
        for block in blocks:
            if not block.strip():
                continue

            dimension = self._map_block_to_dimension(block)
            if dimension is None:
                continue

            score = self._extract_score(block)
            feedback, feedback_blocks = self._extract_feedback_and_blocks(block)
            if not feedback_blocks and scores[dimension].feedback_blocks:
                continue

            scores[dimension] = DimensionScoreDTO(score, feedback, feedback_blocks)
            matched_dimensions.add(dimension)

        return ParsedResponseDTO(scores=scores, matched_dimensions=frozenset(matched_dimensions))

    def _extract_feedback_and_blocks(self, block: str) -> tuple[str, tuple[FeedbackBlockDTO, ...]]:
        cleaned_block = _RECOMMENDATION_TAIL_PATTERN.sub("", block).strip()
        lines = cleaned_block.split("\n")
        header_line = lines[0].strip()
        heading_match = _DIMENSION_HEADING_LEVEL_PATTERN.match(header_line)
        dimension_heading_level = len(heading_match.group(1)) if heading_match is not None else 0

        blocks = self._feedback_structure_parser.parse(
            lines=lines[1:], dimension_heading_level=dimension_heading_level
        )
        if not blocks:
            return self._unscored_dimension_feedback, ()

        feedback = self._format_feedback(blocks)
        if len(feedback) < 10:
            return self._unscored_dimension_feedback, ()

        return feedback, blocks

    def _format_feedback(self, blocks: tuple[FeedbackBlockDTO, ...]) -> str:
        parts: list[str] = []
        for block in blocks:
            if block.kind == FeedbackBlockKind.TITLE:
                parts.append(f"{block.text}:")
            else:
                parts.append(block.text)
        return " ".join(parts)

    def _extract_score(self, block: str) -> float:
        match = _EXPLICIT_SCORE_PATTERN.search(block)
        if match is None:
            return self._infer_score_from_narrative(block)

        score_text = match.group(1) or match.group(2)
        try:
            return max(0.0, min(10.0, float(score_text)))
        except ValueError:
            return self._unscored_dimension_score

    def _infer_score_from_narrative(self, block: str) -> float:
        block_lower = block.lower()
        for keywords, score in _NARRATIVE_SCORE_KEYWORDS:
            if any(keyword in block_lower for keyword in keywords):
                return score
        return self._unscored_dimension_score

    def _map_block_to_dimension(self, block: str) -> QualityDimension | None:
        block_lower = block[:200].lower()
        for dimension, keywords in _DIMENSION_KEYWORDS:
            if any(keyword in block_lower for keyword in keywords):
                return dimension
        return None
