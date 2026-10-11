from unittest import TestCase

from src.domain.enums.allowed_font import AllowedFont
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportSettings(TestCase):
    def test_deployment_fields_are_required(self):
        with self.assertRaises(TypeError):
            DocxReportSettings()

    def test_visual_template_fields_use_static_defaults(self):
        settings = ReportFixtures.make_settings()
        self.assertEqual(settings.font_name, AllowedFont.CALIBRI.value)
        self.assertEqual(settings.table_style, "Light Grid Accent 1")
        self.assertEqual(settings.heading_color_rgb, (0, 51, 102))

    def test_feedback_item_indent_inches_default(self):
        settings = ReportFixtures.make_settings()
        self.assertEqual(settings.feedback_item_indent_inches, (0.25, 0.5, 0.75))

    def test_constructor_arguments_override_deployment_fields(self):
        settings = ReportFixtures.make_settings(words_per_page=300, max_errors_displayed=10)
        self.assertEqual(settings.words_per_page, 300)
        self.assertEqual(settings.max_errors_displayed, 10)

    def test_constructor_overrides_context_truncation_limit(self):
        settings = ReportFixtures.make_settings(context_truncation_limit=10)
        self.assertEqual(settings.context_truncation_limit, 10)

    def test_constructor_overrides_max_replacements(self):
        settings = ReportFixtures.make_settings(max_replacements=1)
        self.assertEqual(settings.max_replacements, 1)
