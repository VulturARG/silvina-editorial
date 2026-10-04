class FeedbackHierarchyTracker:
    """Tracks indentation hierarchy and unindented children mode for list items."""

    def __init__(self) -> None:
        self._previous_top_level_indentation: int | None = None
        self._in_unindented_children_mode = False
        self._child_indentation: int | None = None

    @property
    def in_unindented_children_mode(self) -> bool:
        """Indicate whether the parser is currently inside unindented children mode."""
        return self._in_unindented_children_mode

    def reset(self) -> None:
        """Reset children mode and top-level indentation tracking."""
        self._previous_top_level_indentation = None
        self._in_unindented_children_mode = False
        self._child_indentation = None

    def enter_children_mode(self) -> None:
        """Enter unindented children mode and clear the anchored child indentation."""
        self._in_unindented_children_mode = True
        self._child_indentation = None

    def determine_item_level(self, indentation: int) -> int:
        """Determine whether a list item belongs to level 0 or level 1."""
        if self._in_unindented_children_mode:
            return self._determine_children_mode_level(indentation)
        return self._determine_standard_level(indentation)

    def _determine_children_mode_level(self, indentation: int) -> int:
        if self._child_indentation is None:
            self._child_indentation = indentation
        return 1 if indentation > self._child_indentation else 0

    def _determine_standard_level(self, indentation: int) -> int:
        if (
            self._previous_top_level_indentation is not None
            and indentation > self._previous_top_level_indentation
        ):
            return 1
        self._previous_top_level_indentation = indentation
        return 0
