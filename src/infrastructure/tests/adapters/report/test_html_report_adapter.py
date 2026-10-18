from os import path
from pathlib import Path
from re import search
from tempfile import TemporaryDirectory
from unittest import TestCase

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.domain.enums.quality_dimension import QualityDimension
from src.infrastructure.adapters.report.html_report_adapter import HtmlReportAdapter
from src.infrastructure.fastapi.src.utils.inline_bold_renderer import InlineBoldRenderer
from src.infrastructure.tests.adapters.report.characterization_report_input import (
    CharacterizationReportInput,
)

_INFRASTRUCTURE_DIRECTORY = Path(__file__).resolve().parents[3]
_STANDALONE_TEMPLATES_DIRECTORY = _INFRASTRUCTURE_DIRECTORY / "adapters" / "report" / "templates"
_FASTAPI_TEMPLATES_DIRECTORY = _INFRASTRUCTURE_DIRECTORY / "fastapi" / "templates"
_STYLESHEET_PATH = _INFRASTRUCTURE_DIRECTORY / "fastapi" / "static" / "css" / "silvina.css"
_LOGO_DATA_URI = "data:image/png;base64,iVBORw0KGgo="
_APP_NAME = "Silvina Editorial Assistant"
_APP_VERSION = "1.0.0"


class TestHtmlReportAdapter(TestCase):
    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self._output_path = path.join(self._temporary_directory.name, "report.html")
        self._report_input = CharacterizationReportInput.build()
        self._stylesheet_text = self._read_stylesheet()
        self._adapter = self._make_adapter(logo_data_uri=_LOGO_DATA_URI)

    def tearDown(self):
        self._temporary_directory.cleanup()

    def test_export_returns_true(self):
        result = self._adapter.export(
            report_input=self._report_input, output_path=self._output_path
        )

        self.assertTrue(result)

    def test_export_creates_file(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        self.assertTrue(path.isfile(self._output_path))

    def test_export_writes_full_html_document(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        html = self._read_output()
        self.assertIn("<html", html)
        self.assertIn("<title>Silvina - Asistente Editorial EUMIC</title>", html)

    def test_export_embeds_full_stylesheet(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        html = self._read_output()
        self.assertIn("<style", html)
        self.assertIn(self._stylesheet_text, html)

    def test_export_embeds_logo_data_uri(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        self.assertIn(_LOGO_DATA_URI, self._read_output())

    def test_export_omits_logo_when_data_uri_is_none(self):
        adapter = self._make_adapter(logo_data_uri=None)

        adapter.export(report_input=self._report_input, output_path=self._output_path)

        html = self._read_output()
        self.assertNotIn("<img", html)
        self.assertNotIn("data:image/png", html)

    def test_export_includes_results_partial_with_document_title(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        html = self._read_output()
        self.assertIn(self._report_input.document_content.title, html)
        self.assertIn("Dimensiones Semánticas", html)

    def test_export_renders_footer_with_app_name_and_version(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        self.assertIn(f"{_APP_NAME} v{_APP_VERSION}", self._read_output())

    def test_export_round_trips_accented_spanish_text_as_utf8(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        html = self._read_output()
        self.assertIn("Edición Científica", html)
        self.assertIn("Juan Pérez, María Gómez", html)
        self.assertIn("Próximos pasos", html)
        self.assertIn("Coherencia", html)

    def test_export_has_no_report_download_links(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        self.assertNotIn("/reports/", self._read_output())

    def test_export_has_no_download_attribute(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        self.assertIsNone(search(r"<[^>]*\sdownload[\s>]", self._read_output()))

    def test_export_has_no_script_tags(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        self.assertNotIn("<script", self._read_output())

    def test_export_has_no_external_resource_urls(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        html = self._read_output()
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)

    def test_export_overwrites_existing_file(self):
        with open(self._output_path, "w", encoding="utf-8") as file:
            file.write("stale report content")

        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        html = self._read_output()
        self.assertIn("<html", html)
        self.assertNotIn("stale report content", html)

    def test_export_raises_file_not_found_when_parent_directory_is_missing(self):
        missing_directory_path = path.join(self._temporary_directory.name, "missing", "report.html")

        with self.assertRaises(FileNotFoundError):
            self._adapter.export(
                report_input=self._report_input, output_path=missing_directory_path
            )

    def test_export_shows_prompt_source_when_present(self):
        adapter = self._make_adapter(
            logo_data_uri=_LOGO_DATA_URI,
            prompt_source=PromptSourceDTO(
                base_label="v2", replaced_prompt_names=("alignment_prompt",)
            ),
        )

        adapter.export(report_input=self._report_input, output_path=self._output_path)

        html = self._read_output()
        self.assertIn("Prompts utilizados:", html)
        self.assertIn("v2 + alignment_prompt", html)

    def test_export_omits_prompt_source_when_absent(self):
        self._adapter.export(report_input=self._report_input, output_path=self._output_path)

        self.assertNotIn("Prompts utilizados", self._read_output())

    def _make_adapter(
        self, logo_data_uri: str | None, prompt_source: PromptSourceDTO | None = None
    ) -> HtmlReportAdapter:
        return HtmlReportAdapter(
            template_environment=self._make_template_environment(),
            stylesheet_text=self._stylesheet_text,
            logo_data_uri=logo_data_uri,
            app_name=_APP_NAME,
            app_version=_APP_VERSION,
            prompt_source=prompt_source,
        )

    @staticmethod
    def _make_template_environment() -> Environment:
        environment = Environment(
            loader=FileSystemLoader(
                [str(_STANDALONE_TEMPLATES_DIRECTORY), str(_FASTAPI_TEMPLATES_DIRECTORY)]
            ),
            autoescape=select_autoescape(),
        )
        environment.filters["inline_bold"] = InlineBoldRenderer().render
        environment.filters["dimension_label"] = QualityDimension.label_for
        return environment

    @staticmethod
    def _read_stylesheet() -> str:
        with open(_STYLESHEET_PATH, encoding="utf-8") as file:
            return file.read()

    def _read_output(self) -> str:
        with open(self._output_path, encoding="utf-8") as file:
            return file.read()
