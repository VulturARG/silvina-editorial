from unittest import TestCase

from markupsafe import Markup

from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.enums.recommendation_priority import RecommendationPriority
from src.infrastructure.fastapi.src.config.dependencies import get_templates
from src.infrastructure.fastapi.src.utils.inline_bold_renderer import InlineBoldRenderer
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestInlineBoldRenderer(TestCase):
    """Unit and template-level tests for InlineBoldRenderer and inline_bold filter."""

    def setUp(self) -> None:
        self.renderer = InlineBoldRenderer()

    def test_render_escapes_html_and_ampersand(self) -> None:
        raw_text = '<script>alert("x")</script> & <b>test</b>'
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertNotIn("<script>", str(result))
        self.assertNotIn("<b>", str(result))
        self.assertIn("&lt;script&gt;", str(result))
        self.assertIn("&amp;", str(result))
        self.assertIn("&lt;b&gt;", str(result))

    def test_render_converts_paired_bold_to_strong_tags(self) -> None:
        raw_text = "Este es un **texto en negrita** relevante."
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertEqual(
            str(result),
            "Este es un <strong>texto en negrita</strong> relevante.",
        )

    def test_render_escapes_html_inside_paired_bold(self) -> None:
        raw_text = "**<script>alert('x')</script>**"
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertNotIn("<script>", str(result))
        self.assertIn(
            "<strong>&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt;</strong>", str(result)
        )

    def test_render_leaves_unpaired_bold_markers_literal(self) -> None:
        raw_text = "Esta retroalimentación contiene una marca **huérfana sin par de cierre."
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertEqual(
            str(result),
            "Esta retroalimentación contiene una marca **huérfana sin par de cierre.",
        )

    def test_render_converts_multiple_pairs_and_escapes_quotes_in_real_text(self) -> None:
        real_text = (
            "Fortalezas **Pregunta central bien definida**: Las tres preguntas... "
            '**Estructura anunciada**: La sección "Alcance y organización" orienta... '
            "**Lenguaje accesible**: A pesar..."
        )
        result = self.renderer.render(real_text)

        self.assertIsInstance(result, Markup)
        self.assertIn("<strong>Pregunta central bien definida</strong>", str(result))
        self.assertIn("<strong>Estructura anunciada</strong>", str(result))
        self.assertIn("<strong>Lenguaje accesible</strong>", str(result))
        self.assertIn("&#34;Alcance y organización&#34;", str(result))
        self.assertNotIn("**", str(result))

    def test_render_returns_empty_markup_when_given_none_or_empty_string(self) -> None:
        none_result = self.renderer.render(None)
        empty_result = self.renderer.render("")

        self.assertIsInstance(none_result, Markup)
        self.assertEqual(str(none_result), "")
        self.assertIsInstance(empty_result, Markup)
        self.assertEqual(str(empty_result), "")

    def test_render_does_not_convert_across_newlines(self) -> None:
        multiline_text = (
            "Primera línea con **apertura sin cierre\ny segunda línea con cierre** aquí."
        )
        result = self.renderer.render(multiline_text)

        self.assertIsInstance(result, Markup)
        self.assertNotIn("<strong>", str(result))
        self.assertIn("**apertura sin cierre", str(result))
        self.assertIn("cierre**", str(result))

    def test_render_leaves_empty_bold_markers_literal(self) -> None:
        raw_text = "Texto con cuatro asteriscos **** sin contenido intermedio."
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertNotIn("<strong>", str(result))
        self.assertIn("****", str(result))

    def test_renderer_is_callable_directly(self) -> None:
        raw_text = "Llamada directa con **negrita**."
        result = self.renderer(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertEqual(str(result), "Llamada directa con <strong>negrita</strong>.")

    def test_results_template_renders_bold_feedback_and_removes_literal_markers(self) -> None:
        quality = ReportFixtures.make_quality_mock()
        quality.dimension_scores = {
            "coherencia": {
                "score": 8.5,
                "feedback": "Fortalezas **Pregunta central bien definida**: Las tres preguntas orientan adecuadamente.",
            }
        }
        quality.editorial_suitability = EditorialSuitabilityDTO(
            contribution_verdict="SUSTENTADA",
            contribution_phrase="Aporte claro.",
            contribution_observation="Aporte **significativo** al estado del arte.",
            alignment_verdict="ALINEADO",
            alignment_lines="Línea 1",
            alignment_justification="Alineación **completa** con la línea institucional.",
        )
        recommendation = RecommendationDTO(
            priority=RecommendationPriority.HIGH,
            message="Se debe revisar **inmediatamente** la metodología propuesta.",
        )
        report = ReportFixtures.make_report_input_dto(
            quality=quality,
            recommendations=[recommendation],
        )

        templates = get_templates()
        template = templates.get_template("partials/_results.html")
        rendered = template.render(
            report=report,
            word_filename="informe_analisis.docx",
            json_filename="informe_analisis.json",
        )

        self.assertIn("<strong>Pregunta central bien definida</strong>", rendered)
        self.assertIn("<strong>significativo</strong>", rendered)
        self.assertIn("<strong>completa</strong>", rendered)
        self.assertIn("<strong>inmediatamente</strong>", rendered)
        self.assertNotIn("**Pregunta central bien definida**", rendered)
        self.assertNotIn("**significativo**", rendered)
        self.assertNotIn("**completa**", rendered)
        self.assertNotIn("**inmediatamente**", rendered)

    def test_render_converts_single_asterisk_italics_to_em_tags(self) -> None:
        raw_text = "El texto emplea *correctamente* el *mecanismo* del *cual* depende."
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertEqual(
            str(result),
            "El texto emplea <em>correctamente</em> el <em>mecanismo</em> del <em>cual</em> depende.",
        )

    def test_render_handles_bold_and_italic_in_one_line_and_nested(self) -> None:
        raw_text = "Texto con **negrita** y *cursiva*, más **negrita con *cursiva anidada***."
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertEqual(
            str(result),
            "Texto con <strong>negrita</strong> y <em>cursiva</em>, más <strong>negrita con <em>cursiva anidada</em></strong>.",
        )

    def test_render_preserves_lone_asterisks_and_operators(self) -> None:
        raw_text = "Operación a * b, lista '* item', escala 1 x 10^11, nota* y *unpaired."
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertEqual(
            str(result),
            "Operación a * b, lista &#39;* item&#39;, escala 1 x 10^11, nota* y *unpaired.",
        )

    def test_render_escapes_html_inside_italics(self) -> None:
        raw_text = "*<script>alert('x')</script>*"
        result = self.renderer.render(raw_text)

        self.assertIsInstance(result, Markup)
        self.assertNotIn("<script>", str(result))
        self.assertEqual(
            str(result),
            "<em>&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt;</em>",
        )
