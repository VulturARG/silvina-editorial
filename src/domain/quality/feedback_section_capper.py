from collections.abc import Sequence

from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.quality.feedback_section_cap_state import FeedbackSectionCapState


class FeedbackSectionCapper:
    """Caps feedback blocks per section according to the maximum item limits."""

    def __init__(self, maximum_items_per_section: int = 8) -> None:
        self._maximum_items_per_section = maximum_items_per_section

    def cap_sections(
        self,
        sections: Sequence[tuple[FeedbackBlockDTO | None, list[FeedbackBlockDTO]]],
    ) -> tuple[FeedbackBlockDTO, ...]:
        """Cap top-level and nested blocks for each section and omit empty titled sections."""
        result_blocks: list[FeedbackBlockDTO] = []
        for title, blocks in sections:
            capped_blocks = self._cap_section_blocks(blocks)
            result_blocks.extend(self._build_section_blocks(title, capped_blocks))
        return tuple(result_blocks)

    def _build_section_blocks(
        self,
        title: FeedbackBlockDTO | None,
        kept_blocks: list[FeedbackBlockDTO],
    ) -> list[FeedbackBlockDTO]:
        if title is None:
            return kept_blocks
        if not kept_blocks:
            return []
        return [title, *kept_blocks]

    def _cap_section_blocks(
        self,
        blocks: Sequence[FeedbackBlockDTO],
    ) -> list[FeedbackBlockDTO]:
        cap_state = FeedbackSectionCapState(maximum_items=self._maximum_items_per_section)
        for block in blocks:
            cap_state.process_block(block)
        return cap_state.kept_blocks()
