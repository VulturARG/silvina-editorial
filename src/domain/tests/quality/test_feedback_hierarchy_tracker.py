from unittest import TestCase

from src.domain.quality.feedback_hierarchy_tracker import FeedbackHierarchyTracker


class TestFeedbackHierarchyTracker(TestCase):
    def test_default_state_is_not_in_children_mode(self):
        tracker = FeedbackHierarchyTracker()

        self.assertFalse(tracker.in_unindented_children_mode)

    def test_standard_item_without_previous_indentation_gets_level_zero(self):
        tracker = FeedbackHierarchyTracker()

        level = tracker.determine_item_level(indentation=2)

        self.assertEqual(level, 0)

    def test_standard_item_deeper_than_previous_gets_level_one(self):
        tracker = FeedbackHierarchyTracker()
        tracker.determine_item_level(indentation=0)

        level = tracker.determine_item_level(indentation=2)

        self.assertEqual(level, 1)

    def test_standard_item_not_deeper_than_previous_updates_top_level_and_gets_level_zero(self):
        tracker = FeedbackHierarchyTracker()
        tracker.determine_item_level(indentation=4)

        level = tracker.determine_item_level(indentation=2)

        self.assertEqual(level, 0)
        self.assertEqual(tracker.determine_item_level(indentation=3), 1)

    def test_children_mode_first_child_gets_level_zero_and_anchors_indentation(self):
        tracker = FeedbackHierarchyTracker()
        tracker.enter_children_mode()

        level = tracker.determine_item_level(indentation=2)

        self.assertEqual(level, 0)
        self.assertEqual(tracker.determine_item_level(indentation=4), 1)
        self.assertEqual(tracker.determine_item_level(indentation=2), 0)

    def test_reset_clears_children_mode_and_top_level_indentation(self):
        tracker = FeedbackHierarchyTracker()
        tracker.enter_children_mode()
        tracker.determine_item_level(indentation=4)

        tracker.reset()

        self.assertFalse(tracker.in_unindented_children_mode)
        self.assertEqual(tracker.determine_item_level(indentation=2), 0)
