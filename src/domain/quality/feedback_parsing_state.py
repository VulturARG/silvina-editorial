from src.domain.quality.feedback_hierarchy_tracker import FeedbackHierarchyTracker
from src.domain.quality.feedback_section_accumulator import FeedbackSectionAccumulator


class FeedbackParsingState:
    """Encapsulates per-parse mutable state including the accumulator and hierarchy tracker."""

    def __init__(
        self,
        accumulator: FeedbackSectionAccumulator | None = None,
        hierarchy_tracker: FeedbackHierarchyTracker | None = None,
    ) -> None:
        self.accumulator = accumulator if accumulator is not None else FeedbackSectionAccumulator()
        self.hierarchy_tracker = (
            hierarchy_tracker if hierarchy_tracker is not None else FeedbackHierarchyTracker()
        )
