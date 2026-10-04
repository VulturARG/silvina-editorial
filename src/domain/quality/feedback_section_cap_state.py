from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO


class FeedbackSectionCapState:
    """Manages capping limits and item counters for blocks within a single feedback section."""

    def __init__(self, maximum_items: int = 8) -> None:
        self._maximum_items = maximum_items
        self._kept_blocks: list[FeedbackBlockDTO] = []
        self._top_level_count = 0
        self._level_one_count = 0
        self._parent_kept = True

    def process_block(self, block: FeedbackBlockDTO) -> None:
        """Process a block against the capping limits based on its hierarchy level."""
        if block.level == 0:
            self._process_level_zero(block)
        elif block.level == 1:
            self._process_level_one(block)

    def kept_blocks(self) -> list[FeedbackBlockDTO]:
        """Return a copy of the blocks that survived section capping."""
        return list(self._kept_blocks)

    def _process_level_zero(self, block: FeedbackBlockDTO) -> None:
        if self._top_level_count < self._maximum_items:
            self._kept_blocks.append(block)
            self._top_level_count += 1
            self._level_one_count = 0
            self._parent_kept = True
        else:
            self._level_one_count = 0
            self._parent_kept = False

    def _process_level_one(self, block: FeedbackBlockDTO) -> None:
        if self._parent_kept and self._level_one_count < self._maximum_items:
            self._kept_blocks.append(block)
            self._level_one_count += 1
