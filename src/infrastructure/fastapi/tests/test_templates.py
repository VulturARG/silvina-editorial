from pathlib import Path
from unittest import TestCase

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.enums.publication_verdict import PublicationVerdict
from src.domain.enums.recommendation_priority import RecommendationPriority
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


class TestFastApiTemplates(TestCase):
    """Unit tests for Jinja2 templates rendering and structure."""

    def setUp(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def test_base_template_renders_structure_and_assets(self) -> None:
        template = self.env.get_template("base.html")
        rendered = template.render(title="Silvina Editorial")

        self.assertIn("Silvina", rendered)
        self.assertIn("htmx", rendered)
        self.assertIn("/static/css/silvina.css", rendered)
        self.assertIn("logo-container", rendered)
        self.assertIn("Silvina - Asistente Editorial", rendered)
        self.assertIn("footer", rendered)

    def test_index_template_renders_upload_form_and_indicator(self) -> None:
        template = self.env.get_template("index.html")
        rendered = template.render()

        self.assertIn('hx-post="/analyze"', rendered)
        self.assertIn('enctype="multipart/form-data"', rendered)
        self.assertIn('type="file"', rendered)
        self.assertIn(".docx", rendered)
        self.assertIn('hx-indicator="#loading-indicator"', rendered)
        self.assertIn('id="loading-indicator"', rendered)
        self.assertIn("htmx-indicator", rendered)
        self.assertIn('id="results-container"', rendered)
        self.assertIn("Paso 1: Cargar Documento", rendered)
        self.assertIn("Paso 2: Resultados del Análisis", rendered)

    def test_results_template_renders_approved_verdict(self) -> None:
        report = ReportFixtures.make_report_input_dto(
            verdict=ReportFixtures.make_verdict_dto(PublicationVerdict.APPROVED)
        )
        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="sample_analisis.docx",
            json_filename="sample_analisis.json",
        )

        self.assertIn("APTO PARA PUBLICACIÓN", rendered)
        self.assertIn("✅", rendered)
        self.assertIn(report.document_content.title, rendered)
        self.assertIn(str(report.document_content.word_count), rendered)
        self.assertIn("Gramática y Ortografía", rendered)
        self.assertIn("Calidad Semántica", rendered)
        self.assertIn("Errores gramaticales", rendered)
        self.assertIn("Errores APA 7", rendered)
        self.assertIn("Citas sin referencia", rendered)
        self.assertIn("Secciones faltantes", rendered)
        self.assertIn("Dimensiones Semánticas", rendered)
        self.assertIn("/reports/sample_analisis.docx", rendered)
        self.assertIn("/reports/sample_analisis.json", rendered)

    def test_results_template_renders_warning_and_critical_verdicts(self) -> None:
        template = self.env.get_template("partials/_results.html")

        warning_report = ReportFixtures.make_report_input_dto(
            verdict=ReportFixtures.make_verdict_dto(PublicationVerdict.WARNING)
        )
        rendered_warning = template.render(
            report=warning_report,
            word_filename="warn_analisis.docx",
            json_filename="warn_analisis.json",
        )
        self.assertIn("REQUIERE REVISIÓN", rendered_warning)
        self.assertIn("⚠️", rendered_warning)

        critical_report = ReportFixtures.make_report_input_dto(
            verdict=ReportFixtures.make_verdict_dto(PublicationVerdict.CRITICAL)
        )
        rendered_critical = template.render(
            report=critical_report,
            word_filename="crit_analisis.docx",
            json_filename="crit_analisis.json",
        )
        self.assertIn("NO APTO", rendered_critical)
        self.assertIn("❌", rendered_critical)

    def test_results_template_renders_critical_issues_when_present(self) -> None:
        high_rec = RecommendationDTO(
            priority=RecommendationPriority.HIGH,
            message="El manuscrito no incluye metodología explícita.",
        )
        report = ReportFixtures.make_report_input_dto(recommendations=[high_rec])
        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="crit_rec_analisis.docx",
            json_filename="crit_rec_analisis.json",
        )

        self.assertIn("Problemas Críticos Detectados", rendered)
        self.assertIn("El manuscrito no incluye metodología explícita.", rendered)

    def test_results_template_renders_editorial_suitability_when_present(self) -> None:
        suitability = EditorialSuitabilityDTO(
            contribution_verdict="SUSTENTADA",
            contribution_phrase="Aporte metodológico claro.",
            contribution_observation="Observación de prueba sobre la contribución.",
            alignment_verdict="ALINEADO",
            alignment_lines="Línea 1: Educación y Sociedad",
            alignment_justification="Justificación de prueba sobre la alineación.",
        )
        quality = ReportFixtures.make_quality_mock()
        quality.editorial_suitability = suitability
        report = ReportFixtures.make_report_input_dto(quality=quality)

        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="suitability_analisis.docx",
            json_filename="suitability_analisis.json",
        )

        self.assertIn("Pertinencia Editorial", rendered)
        self.assertIn("SUSTENTADA", rendered)
        self.assertIn("ALINEADO", rendered)
        self.assertIn("Educación y Sociedad", rendered)

    def test_error_template_renders_error_message_and_callout(self) -> None:
        template = self.env.get_template("partials/_error.html")
        rendered = template.render(error_message="El documento está vacío o dañado.")

        self.assertIn("El documento está vacío o dañado.", rendered)
        self.assertIn("error-callout", rendered)
