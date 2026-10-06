from unittest import TestCase

from src.domain.quality.feedback_hierarchy_tracker import FeedbackHierarchyTracker
from src.domain.quality.feedback_parsing_state import FeedbackParsingState
from src.domain.quality.feedback_section_accumulator import FeedbackSectionAccumulator


class TestFeedbackParsingState(TestCase):
    def test_instantiates_fresh_accumulator_and_hierarchy_tracker(self):
        state = FeedbackParsingState()

        self.assertIsInstance(state.accumulator, FeedbackSectionAccumulator)
        self.assertIsInstance(state.hierarchy_tracker, FeedbackHierarchyTracker)

    def test_accepts_injected_accumulator_and_tracker_for_testing(self):
        accumulator = FeedbackSectionAccumulator()
        tracker = FeedbackHierarchyTracker()
        state = FeedbackParsingState(accumulator=accumulator, hierarchy_tracker=tracker)

        self.assertIs(state.accumulator, accumulator)
        self.assertIs(state.hierarchy_tracker, tracker)
