from unittest import TestCase

from src.domain.enums.severity_level import SeverityLevel


class TestSeverityLevel(TestCase):
    def test_severity_level_importable_independently(self):
        self.assertEqual(SeverityLevel.CRITICAL.value, "critical")

    def test_members_and_values(self):
        self.assertEqual(SeverityLevel.INFO.value, "info")
        self.assertEqual(SeverityLevel.WARNING.value, "warning")
        self.assertEqual(SeverityLevel.ERROR.value, "error")
        self.assertEqual(SeverityLevel.CRITICAL.value, "critical")

    def test_member_count(self):
        self.assertEqual(len(SeverityLevel), 4)

    def test_label_is_spanish_for_every_severity(self):
        self.assertEqual(SeverityLevel.INFO.label, "Información")
        self.assertEqual(SeverityLevel.WARNING.label, "Advertencia")
        self.assertEqual(SeverityLevel.ERROR.label, "Error")
        self.assertEqual(SeverityLevel.CRITICAL.label, "Crítico")
