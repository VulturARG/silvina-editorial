from pathlib import Path
from re import search
from unittest import TestCase

from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.enums.publication_verdict import PublicationVerdict
from src.domain.enums.recommendation_priority import RecommendationPriority
from src.infrastructure.fastapi.src.config.dependencies import (
    get_env_config,
    get_templates,
)
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestFastApiTemplates(TestCase):
    """Unit tests for Jinja2 templates rendering and structure."""

    def setUp(self) -> None:
        self.templates = get_templates()
        self.env = self.templates.env

    def test_base_template_renders_structure_and_assets(self) -> None:
        template = self.env.get_template("base.html")
        rendered = template.render(title="Silvina Editorial")

        self.assertIn("Silvina", rendered)
        self.assertIn("htmx", rendered)
        self.assertIn("/static/css/silvina.css", rendered)
        self.assertIn("logo-container", rendered)
        self.assertIn("Silvina - Asistente Editorial", rendered)
        self.assertIn("footer", rendered)

    def test_base_template_renders_stylesheet_with_cache_busting_version(self) -> None:
        templates = get_templates()
        template = templates.get_template("base.html")
        rendered = template.render()

        self.assertIn("silvina.css?v=", rendered)

    def test_base_template_renders_configured_version_and_application_name(self) -> None:
        templates = get_templates()
        template = templates.get_template("base.html")
        rendered = template.render()
        environment_configuration = get_env_config()

        self.assertIn(environment_configuration.silvina_app_name, rendered)
        self.assertIn(f"v{environment_configuration.silvina_version}", rendered)
        self.assertNotIn("v0.8", rendered)

    def test_index_page_renders_configured_version_and_application_name(self) -> None:
        templates = get_templates()
        template = templates.get_template("index.html")
        rendered = template.render()
        environment_configuration = get_env_config()

        self.assertIn(environment_configuration.silvina_app_name, rendered)
        self.assertIn(f"v{environment_configuration.silvina_version}", rendered)
        self.assertNotIn("v0.8", rendered)

    def test_index_template_renders_upload_form_and_indicator(self) -> None:
        template = self.env.get_template("index.html")
        rendered = template.render()

        self.assertIn('hx-post="/analyze"', rendered)
        self.assertIn('enctype="multipart/form-data"', rendered)
        self.assertIn('type="file"', rendered)
        self.assertIn(".docx", rendered)
        self.assertIn('hx-indicator="#loading-indicator"', rendered)
        self.assertIn('hx-disabled-elt="find button[type=submit]"', rendered)
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

    def test_results_template_renders_inline_bold_across_feedback_fields(self) -> None:
        quality = ReportFixtures.make_quality_mock()
        quality.dimension_scores = {
            "claridad": {
                "score": 9.0,
                "feedback": "Dimensión con **claridad conceptual excelente** demostrada.",
            }
        }
        quality.editorial_suitability = EditorialSuitabilityDTO(
            contribution_verdict="SUSTENTADA",
            contribution_phrase="Aporte metodológico claro.",
            contribution_observation="Aporte **altamente sustentado** en datos.",
            alignment_verdict="ALINEADO",
            alignment_lines="Línea 1",
            alignment_justification="Tema **perfectamente alineado** con el área.",
        )
        recommendation = RecommendationDTO(
            priority=RecommendationPriority.HIGH,
            message="Problema crítico: resolver **de inmediato** la sección.",
        )
        report = ReportFixtures.make_report_input_dto(
            quality=quality,
            recommendations=[recommendation],
        )

        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="bold_analisis.docx",
            json_filename="bold_analisis.json",
        )

        self.assertIn("<strong>claridad conceptual excelente</strong>", rendered)
        self.assertIn("<strong>altamente sustentado</strong>", rendered)
        self.assertIn("<strong>perfectamente alineado</strong>", rendered)
        self.assertIn("<strong>de inmediato</strong>", rendered)
        self.assertNotIn("**claridad conceptual excelente**", rendered)
        self.assertNotIn("**altamente sustentado**", rendered)
        self.assertNotIn("**perfectamente alineado**", rendered)
        self.assertNotIn("**de inmediato**", rendered)

    def test_results_template_renders_structured_feedback_blocks_when_present(self) -> None:
        quality = ReportFixtures.make_quality_mock()
        quality.dimension_scores = {
            "claridad": {
                "score": 9.0,
                "feedback": "Texto plano de respaldo.",
                "feedback_blocks": [
                    {
                        "kind": "title",
                        "text": "Fortalezas",
                        "level": 0,
                        "marker": "",
                    },
                    {
                        "kind": "item",
                        "text": "Item con <script>alerta</script> y frase **muy relevante**.",
                        "level": 0,
                        "marker": "•",
                    },
                    {
                        "kind": "item",
                        "text": "Segundo item numerado.",
                        "level": 0,
                        "marker": "1.",
                    },
                    {
                        "kind": "item",
                        "text": "Detalle anidado nivel uno.",
                        "level": 1,
                        "marker": "•",
                    },
                ],
            }
        }
        report = ReportFixtures.make_report_input_dto(quality=quality)

        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="blocks_analisis.docx",
            json_filename="blocks_analisis.json",
        )

        self.assertIn('<div class="feedback-block-title">Fortalezas</div>', rendered)
        self.assertIn("feedback-block-marker", rendered)
        self.assertIn("•", rendered)
        self.assertIn("1.", rendered)
        self.assertIn("<strong>muy relevante</strong>", rendered)
        self.assertNotIn("**muy relevante**", rendered)
        self.assertIn("&lt;script&gt;alerta&lt;/script&gt;", rendered)
        self.assertNotIn("<script>alerta</script>", rendered)
        self.assertIn("level-1", rendered)
        self.assertNotIn("Texto plano de respaldo.", rendered)

    def test_results_template_renders_flat_feedback_when_blocks_empty(self) -> None:
        quality = ReportFixtures.make_quality_mock()
        quality.dimension_scores = {
            "claridad": {
                "score": 8.0,
                "feedback": "Dimensión clásica con **texto plano**.",
                "feedback_blocks": [],
            }
        }
        report = ReportFixtures.make_report_input_dto(quality=quality)

        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="flat_analisis.docx",
            json_filename="flat_analisis.json",
        )

        self.assertIn("Dimensión clásica con <strong>texto plano</strong>.", rendered)
        self.assertNotIn("feedback-block-title", rendered)
        self.assertNotIn("feedback-block-item", rendered)

    def test_results_template_renders_level_two_block_with_level_two_class(self) -> None:
        quality = ReportFixtures.make_quality_mock()
        quality.dimension_scores = {
            "claridad": {
                "score": 9.0,
                "feedback": "Texto plano de respaldo.",
                "feedback_blocks": [
                    {
                        "kind": "item",
                        "text": "Elemento hijo de segundo nivel.",
                        "level": 2,
                        "marker": "•",
                    },
                    {
                        "kind": "text",
                        "text": "Párrafo de segundo nivel.",
                        "level": 2,
                        "marker": "",
                    },
                ],
            }
        }
        report = ReportFixtures.make_report_input_dto(quality=quality)

        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="blocks_analisis.docx",
            json_filename="blocks_analisis.json",
        )

        self.assertIn("feedback-block-item level-2", rendered)
        self.assertIn("feedback-block-text level-2", rendered)

    def test_results_template_renders_feedback_block_items_structure_for_all_levels(self) -> None:
        """Render results template and assert DOM structure for item markers across levels 0, 1, 2."""
        quality = ReportFixtures.make_quality_mock()
        quality.dimension_scores = {
            "claridad": {
                "score": 9.0,
                "feedback": "Texto plano de respaldo.",
                "feedback_blocks": [
                    {
                        "kind": "item",
                        "text": "Elemento nivel cero.",
                        "level": 0,
                        "marker": "•",
                    },
                    {
                        "kind": "item",
                        "text": "Elemento nivel uno.",
                        "level": 1,
                        "marker": "1.",
                    },
                    {
                        "kind": "item",
                        "text": "Elemento nivel dos.",
                        "level": 2,
                        "marker": "10.",
                    },
                ],
            }
        }
        report = ReportFixtures.make_report_input_dto(quality=quality)
        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="blocks_analisis.docx",
            json_filename="blocks_analisis.json",
        )

        self.assertRegex(
            rendered,
            r'<div class="feedback-block-item">\s*<span class="feedback-block-marker">•</span>\s*Elemento nivel cero\.',
        )
        self.assertRegex(
            rendered,
            r'<div class="feedback-block-item level-1">\s*<span class="feedback-block-marker">1\.</span>\s*Elemento nivel uno\.',
        )
        self.assertRegex(
            rendered,
            r'<div class="feedback-block-item level-2">\s*<span class="feedback-block-marker">10\.</span>\s*Elemento nivel dos\.',
        )

    def test_stylesheet_defines_hanging_indent_rules_for_feedback_block_items(self) -> None:
        """Verify stylesheet defines negative text-indent, marker zero indent, and text block rules."""
        stylesheet_path = Path(__file__).resolve().parent.parent / "static" / "css" / "silvina.css"
        stylesheet_content = stylesheet_path.read_text(encoding="utf-8")

        hanging_indent_pattern = (
            r"text-indent\s*:\s*calc\(-1\s*\*\s*var\(--feedback-marker-width\)\)"
        )
        marker_width_padding_pattern = r"padding-left\s*:[^;]*var\(--feedback-marker-width\)"

        level_zero_match = search(r"\.feedback-block-item\s*\{([^}]+)\}", stylesheet_content)
        self.assertIsNotNone(level_zero_match)
        assert level_zero_match is not None
        level_zero_body = level_zero_match.group(1)
        self.assertRegex(level_zero_body, hanging_indent_pattern)
        self.assertRegex(level_zero_body, marker_width_padding_pattern)

        level_one_match = search(
            r"\.feedback-block-item\.level-1\s*\{([^}]+)\}", stylesheet_content
        )
        self.assertIsNotNone(level_one_match)
        assert level_one_match is not None
        level_one_body = level_one_match.group(1)
        self.assertRegex(level_one_body, hanging_indent_pattern)
        self.assertRegex(level_one_body, marker_width_padding_pattern)

        level_two_match = search(
            r"\.feedback-block-item\.level-2\s*\{([^}]+)\}", stylesheet_content
        )
        self.assertIsNotNone(level_two_match)
        assert level_two_match is not None
        level_two_body = level_two_match.group(1)
        self.assertRegex(level_two_body, hanging_indent_pattern)
        self.assertRegex(level_two_body, marker_width_padding_pattern)

        marker_match = search(r"\.feedback-block-marker\s*\{([^}]+)\}", stylesheet_content)
        self.assertIsNotNone(marker_match)
        assert marker_match is not None
        marker_body = marker_match.group(1)
        self.assertRegex(marker_body, r"display\s*:\s*inline-block")
        self.assertRegex(marker_body, r"min-width\s*:[^;]*var\(--feedback-marker-width\)")
        self.assertRegex(marker_body, r"text-indent\s*:\s*0\b")

        for selector in (
            r"\.feedback-block-text\s*\{([^}]+)\}",
            r"\.feedback-block-text\.level-1\s*\{([^}]+)\}",
            r"\.feedback-block-text\.level-2\s*\{([^}]+)\}",
        ):
            text_match = search(selector, stylesheet_content)
            self.assertIsNotNone(text_match)
            assert text_match is not None
            self.assertNotIn("text-indent", text_match.group(1))

    def test_results_template_renders_dimension_label_with_accent_for_argumentacion(
        self,
    ) -> None:
        quality = ReportFixtures.make_quality_mock()
        quality.dimension_scores = {
            "argumentacion": {
                "score": 8.0,
                "feedback": "Análisis de la dimensión.",
            }
        }
        report = ReportFixtures.make_report_input_dto(quality=quality)
        template = self.env.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="informe.docx",
            json_filename="informe.json",
        )

        self.assertIn("Argumentación", rendered)
        self.assertNotIn("Argumentacion", rendered)
