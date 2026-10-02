from unittest import TestCase

from src.domain.enums.classification_confidence import ClassificationConfidence


class TestClassificationConfidence(TestCase):
    """Unit tests for ClassificationConfidence enumeration."""

    def test_enum_has_exactly_five_members_with_english_names(self):
        self.assertEqual(len(ClassificationConfidence), 5)
        member_names = {member.name for member in ClassificationConfidence}
        self.assertEqual(
            member_names,
            {
                "IMRYD_OVERRIDE",
                "FULL_SIGNAL_MATCH",
                "RECENT_BIBLIOGRAPHY_SUPPORT",
                "COMPLETE_BIBLIOGRAPHY_SUPPORT",
                "SUFFICIENT_REFERENCE_COUNT",
            },
        )
        member_values = {member.value for member in ClassificationConfidence}
        self.assertEqual(member_values, {0.95, 0.90, 0.86, 0.85, 0.83})

    def test_enum_members_behave_as_plain_floats(self):
        self.assertEqual(ClassificationConfidence.IMRYD_OVERRIDE, 0.95)
        self.assertEqual(ClassificationConfidence.IMRYD_OVERRIDE * 2, 1.90)

    def test_format_percentage_for_specific_members(self):
        self.assertEqual(format(ClassificationConfidence.FULL_SIGNAL_MATCH, ".1%"), "90.0%")
        self.assertEqual(format(ClassificationConfidence.IMRYD_OVERRIDE, ".1%"), "95.0%")

    def test_f_string_formatting_matches_format_function(self):
        self.assertEqual(f"{ClassificationConfidence.FULL_SIGNAL_MATCH:.1%}", "90.0%")
        self.assertEqual(f"{ClassificationConfidence.IMRYD_OVERRIDE:.1%}", "95.0%")

    def test_members_compare_equal_to_floats_and_convert_to_float(self):
        for member in ClassificationConfidence:
            self.assertEqual(member, member.value)
            converted_float = float(member)
            self.assertEqual(converted_float, member.value)
            self.assertIsInstance(converted_float, float)

    def test_each_member_formats_correctly(self):
        expected_percentages = {
            ClassificationConfidence.IMRYD_OVERRIDE: "95.0%",
            ClassificationConfidence.FULL_SIGNAL_MATCH: "90.0%",
            ClassificationConfidence.RECENT_BIBLIOGRAPHY_SUPPORT: "86.0%",
            ClassificationConfidence.COMPLETE_BIBLIOGRAPHY_SUPPORT: "85.0%",
            ClassificationConfidence.SUFFICIENT_REFERENCE_COUNT: "83.0%",
        }
        for member, expected_percentage in expected_percentages.items():
            self.assertEqual(format(member, ".1%"), expected_percentage)
            self.assertEqual(f"{member:.1%}", expected_percentage)
