from unittest import TestCase

from src.domain.enums.editorial_alignment_verdict import EditorialAlignmentVerdict


class TestEditorialAlignmentVerdict(TestCase):
    def test_members_match_expected_alignment_labels(self):
        self.assertEqual(EditorialAlignmentVerdict.ALIGNED.value, "ALINEADO")
        self.assertEqual(EditorialAlignmentVerdict.PARTIALLY_ALIGNED.value, "PARCIALMENTE ALINEADO")
        self.assertEqual(EditorialAlignmentVerdict.NOT_ALIGNED.value, "NO ALINEADO")

    def test_member_count(self):
        self.assertEqual(len(EditorialAlignmentVerdict), 3)
