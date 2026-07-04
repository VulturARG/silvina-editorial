"""
E2E test for gradio_app.py using Gradio test client.
Skipped when gradio testing client is unavailable.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Inject language_tool_python mock before any import
if "language_tool_python" not in sys.modules:
    _mock_ltp = MagicMock()
    _mock_lt_instance = MagicMock()
    _mock_lt_instance.check.return_value = []
    _mock_ltp.LanguageTool.return_value = _mock_lt_instance
    sys.modules["language_tool_python"] = _mock_ltp

FIXTURE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "fixtures", "capacidades_razonamiento_emergente_LLMs.docx"
    )
)

# Detect if gradio Client is available
try:
    from gradio.test_utils import get_fake_upload_file  # older gradio  # noqa: F401

    _GRADIO_TEST_AVAILABLE = True
except ImportError:
    try:
        from gradio import Client as GradioClient  # noqa: F401

        _GRADIO_TEST_AVAILABLE = True
    except ImportError:
        _GRADIO_TEST_AVAILABLE = False


@unittest.skipUnless(_GRADIO_TEST_AVAILABLE, "gradio test client not available in this environment")
class TestGradioAppE2E(unittest.TestCase):
    """
    Launches the Gradio app in test mode (blocks=False) and submits a .docx
    through its file-upload interface. Validates the response structure.
    """

    @classmethod
    def setUpClass(cls):
        """Launch the Gradio app in test/demo mode."""
        from unittest.mock import patch, MagicMock

        mock_client = MagicMock()
        mock_client.generate.return_value = {"response": "S4: SI\nS5: SI\nS6: SI"}

        cls._patches = [
            patch("ollama.Client", return_value=mock_client),
            patch("language_tool_python.LanguageTool", return_value=MagicMock()),
            patch("data_access.word_counter.WIN32COM_AVAILABLE", False),
        ]
        for p in cls._patches:
            p.start()

        try:
            import gradio_app

            # Try to get the Gradio Blocks object without launching
            cls.demo = getattr(gradio_app, "demo", None)
            cls.app_available = cls.demo is not None
        except Exception:
            cls.app_available = False

    @classmethod
    def tearDownClass(cls):
        for p in cls._patches:
            p.stop()

    @unittest.skipUnless(os.path.exists(FIXTURE_PATH), "Fixture .docx not available")
    def test_gradio_app_object_exists(self):
        """The module must export a 'demo' Blocks object."""
        self.assertTrue(
            self.app_available, "gradio_app.py must expose a 'demo' Gradio Blocks object"
        )

    def test_fixture_exists_for_upload(self):
        self.assertTrue(os.path.exists(FIXTURE_PATH))


def _build_report_input_dto():
    """Build a ReportInputDTO fixture for testing UI-facing helpers."""
    from src.domain.dtos.apa_validation_result_dto import ApaValidationResultDTO
    from src.domain.dtos.apa_violation_dto import ApaViolationDTO
    from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
    from src.domain.dtos.classification_result_dto import ClassificationResultDTO
    from src.domain.dtos.document_content_dto import DocumentContentDTO
    from src.domain.dtos.grammar_check_result_dto import GrammarCheckResultDTO
    from src.domain.dtos.grammar_error_dto import GrammarErrorDTO
    from src.domain.dtos.publication_verdict_dto import PublicationVerdictDTO
    from src.domain.dtos.quality_result_dto import QualityResultDTO
    from src.domain.dtos.recommendation_dto import RecommendationDTO
    from src.domain.dtos.report_input_dto import ReportInputDTO
    from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
    from src.domain.enums.apa_error_type import ApaErrorType
    from src.domain.enums.article_size import ArticleSize
    from src.domain.enums.article_type import ArticleType
    from src.domain.enums.publication_verdict import PublicationVerdict
    from src.domain.enums.quality_level import QualityLevel
    from src.domain.enums.recommendation_priority import RecommendationPriority

    document_content = DocumentContentDTO(
        word_count=1500,
        char_count=9000,
        title="El Impacto de la IA en la Educación",
        authors="Ana Perez",
    )
    classification = ClassificationResultDTO.create(
        article_type=ArticleType.SCIENTIFIC,
        article_size=ArticleSize.SHORT,
        confidence=0.9,
        reasoning="Contiene metodología IMRyD",
    )
    quality = QualityResultDTO(
        overall_score=7.5,
        quality_level=QualityLevel.GOOD,
        dimension_scores={
            "coherencia": {"score": 8.0, "feedback": "Argumentación clara"},
        },
    )
    grammar = GrammarCheckResultDTO(
        score=6.5,
        feedback="Se detectaron algunos errores menores",
        errors=[
            GrammarErrorDTO(
                number=1,
                message="Error de concordancia",
                context="algun contexto",
                offset=5,
                length=4,
                replacements=["algún"],
            )
        ],
    )
    structure = StructureValidationResultDTO(
        is_valid=False,
        missing_sections=["Conclusiones"],
        section_details={},
    )
    citations = CitationAnalysisResultDTO(
        total_citations=4,
        total_references=4,
        matched_count=3,
        unmatched_count=1,
        citations_by_type={"author_year": 4},
        unmatched_citations=["Doe 2019"],
    )
    apa_validation = ApaValidationResultDTO(
        is_valid=False,
        violation_count=1,
        violations=[
            ApaViolationDTO(
                citation_text="Doe 2019",
                error_type=ApaErrorType.YEAR_FORMAT_ERROR,
                location=1,
                explanation="Falta el año entre paréntesis",
                correction="(Doe, 2019)",
            )
        ],
    )
    recommendations = [
        RecommendationDTO(priority=RecommendationPriority.HIGH, message="Corregir citas APA"),
        RecommendationDTO(priority=RecommendationPriority.LOW, message="Revisar estilo"),
    ]
    verdict = PublicationVerdictDTO(
        verdict=PublicationVerdict.WARNING,
        message="El documento requiere revisión antes de publicarse",
    )

    return ReportInputDTO(
        filename="/tmp/some/path/documento.docx",
        document_content=document_content,
        classification=classification,
        quality=quality,
        grammar=grammar,
        structure=structure,
        citations=citations,
        apa_validation=apa_validation,
        recommendations=recommendations,
        verdict=verdict,
        eumic_violations=[],
    )


class TestCreateResultsDisplay(unittest.TestCase):
    """Unit tests for gradio_app.create_results_display bound to ReportInputDTO."""

    @classmethod
    def setUpClass(cls):
        from unittest.mock import patch, MagicMock

        cls._patches = [
            patch("ollama.Client", return_value=MagicMock()),
            patch("language_tool_python.LanguageTool", return_value=MagicMock()),
        ]
        for p in cls._patches:
            p.start()
        import gradio_app

        cls.gradio_app = gradio_app

    @classmethod
    def tearDownClass(cls):
        for p in cls._patches:
            p.stop()

    def test_binds_document_metadata(self):
        report = _build_report_input_dto()
        html = self.gradio_app.create_results_display(report)
        self.assertIn("El Impacto de la IA en la Educación", html)
        self.assertIn("Ana Perez", html)
        self.assertIn("1,500", html)
        self.assertIn("CIENTÍFICO", html)

    def test_binds_verdict_status_and_message(self):
        report = _build_report_input_dto()
        html = self.gradio_app.create_results_display(report)
        self.assertIn("REQUIERE REVISIÓN", html)
        self.assertIn("El documento requiere revisión antes de publicarse", html)

    def test_binds_scores_and_error_counts(self):
        report = _build_report_input_dto()
        html = self.gradio_app.create_results_display(report)
        self.assertIn("6.5", html)  # grammar score
        self.assertIn("7.5", html)  # semantic score
        self.assertIn(">1<", html)  # grammar errors count and apa errors count
        self.assertIn("Argumentación clara", html)

    def test_filters_critical_recommendations_by_high_priority(self):
        report = _build_report_input_dto()
        html = self.gradio_app.create_results_display(report)
        self.assertIn("Corregir citas APA", html)
        self.assertNotIn("Revisar estilo", html)


class TestPrepareForJson(unittest.TestCase):
    """Unit tests for gradio_app._prepare_for_json recursive serializer helper."""

    @classmethod
    def setUpClass(cls):
        from unittest.mock import patch, MagicMock

        cls._patches = [
            patch("ollama.Client", return_value=MagicMock()),
            patch("language_tool_python.LanguageTool", return_value=MagicMock()),
        ]
        for p in cls._patches:
            p.start()
        import gradio_app

        cls.gradio_app = gradio_app

    @classmethod
    def tearDownClass(cls):
        for p in cls._patches:
            p.stop()

    def test_converts_enum_to_its_value(self):
        from src.domain.enums.recommendation_priority import RecommendationPriority

        result = self.gradio_app._prepare_for_json(RecommendationPriority.HIGH)
        self.assertEqual(result, "alta")

    def test_converts_datetime_to_isoformat(self):
        from datetime import datetime

        moment = datetime(2026, 7, 1, 12, 30, 0)
        result = self.gradio_app._prepare_for_json(moment)
        self.assertEqual(result, moment.isoformat())

    def test_converts_nested_dto_recursively(self):
        from src.domain.dtos.publication_verdict_dto import PublicationVerdictDTO
        from src.domain.enums.publication_verdict import PublicationVerdict

        dto = PublicationVerdictDTO(verdict=PublicationVerdict.APPROVED, message="Apto")
        result = self.gradio_app._prepare_for_json(dto)
        self.assertEqual(result, {"verdict": "aprobado", "message": "Apto"})

    def test_converts_dict_and_list_containers_recursively(self):
        from src.domain.enums.recommendation_priority import RecommendationPriority

        data = {
            "items": [RecommendationPriority.HIGH, RecommendationPriority.LOW],
            "label": "prioridades",
        }
        result = self.gradio_app._prepare_for_json(data)
        self.assertEqual(result, {"items": ["alta", "baja"], "label": "prioridades"})

    def test_passes_through_plain_values_unchanged(self):
        self.assertEqual(self.gradio_app._prepare_for_json(42), 42)
        self.assertEqual(self.gradio_app._prepare_for_json("texto"), "texto")


class TestProcessDocumentExceptionHandling(unittest.TestCase):
    """Unit tests for process_document's domain vs. generic exception handling."""

    @classmethod
    def setUpClass(cls):
        from unittest.mock import patch, MagicMock

        cls._patches = [
            patch("ollama.Client", return_value=MagicMock()),
            patch("language_tool_python.LanguageTool", return_value=MagicMock()),
        ]
        for p in cls._patches:
            p.start()
        import gradio_app

        cls.gradio_app = gradio_app

    @classmethod
    def tearDownClass(cls):
        for p in cls._patches:
            p.stop()

    def test_base_src_error_returns_clean_domain_message_without_traceback(self):
        from unittest.mock import patch, MagicMock
        from src.domain.exceptions.base_src_error import SrcGenericError

        uploaded_file = MagicMock()
        uploaded_file.name = "documento.docx"

        with patch.object(
            self.gradio_app.analyze_document_use_case,
            "execute",
            side_effect=SrcGenericError("Formato de archivo inválido"),
        ):
            status, html, word_path, json_path, doc_name, _btn = self.gradio_app.process_document(
                uploaded_file
            )

        self.assertIn("Error de validación", status)
        self.assertIn("Formato de archivo inválido", status)
        self.assertIsNone(word_path)
        self.assertIsNone(json_path)

    def test_generic_exception_returns_system_error_message(self):
        from unittest.mock import patch, MagicMock

        uploaded_file = MagicMock()
        uploaded_file.name = "documento.docx"

        with patch.object(
            self.gradio_app.analyze_document_use_case,
            "execute",
            side_effect=RuntimeError("disk full"),
        ):
            status, html, word_path, json_path, doc_name, _btn = self.gradio_app.process_document(
                uploaded_file
            )

        self.assertIn("Error al procesar el documento", status)
        self.assertIn("disk full", status)
        self.assertIsNone(word_path)
        self.assertIsNone(json_path)


@unittest.skip("Gradio test client not available — skipping full UI integration test")
class TestGradioClientE2E(unittest.TestCase):
    """
    Full browser-less Gradio client test. Requires gradio >= 3.x Client API.
    Skip annotation kept so the test runner is aware of this pending test.
    """

    def test_upload_docx_returns_response(self):
        """Upload fixture .docx → response dict with analysis results."""
        from unittest.mock import patch, MagicMock

        mock_client = MagicMock()
        mock_client.generate.return_value = {"response": "S4: SI\nS5: SI\nS6: SI"}

        with (
            patch("ollama.Client", return_value=mock_client),
            patch("language_tool_python.LanguageTool", return_value=MagicMock()),
            patch("data_access.word_counter.WIN32COM_AVAILABLE", False),
        ):
            import gradio_app

            demo = gradio_app.demo

            with demo.test() as test_client:
                result = test_client.predict(FIXTURE_PATH, api_name="/analyze")

        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
