from unittest import TestCase
from unittest.mock import MagicMock

from src.domain.enums.eumic_category import EumicCategory
from src.domain.enums.severity_level import SeverityLevel
from src.infrastructure.adapters.document.eumic_violation_factory import (
    EumicViolationFactory,
)


class TestEumicViolationFactory(TestCase):
    """Verifies factory message formatting for EUMIC format violations."""

    def test_non_standard_fonts_includes_allowed_and_detected_fonts_in_details(self):
        violation = EumicViolationFactory.non_standard_fonts(
            detected_fonts={"Comic Sans MS"},
            allowed_fonts=("Times New Roman", "Arial", "Calibri"),
        )
        self.assertEqual(violation.category, EumicCategory.FORMAT)
        self.assertEqual(violation.severity, SeverityLevel.WARNING)
        self.assertEqual(
            violation.details,
            "Usar una de las fuentes permitidas: Times New Roman, Arial, Calibri. Detectadas: Comic Sans MS",
        )

    def test_variable_font_sizes_includes_required_size_and_detected_sizes(self):
        size_mock = MagicMock()
        size_mock.pt = 10.0
        violation = EumicViolationFactory.variable_font_sizes(
            non_standard_sizes=[size_mock],
            required_size_pt=12.0,
        )
        self.assertEqual(violation.category, EumicCategory.FORMAT)
        self.assertEqual(violation.severity, SeverityLevel.INFO)
        self.assertEqual(
            violation.details,
            "Predominantemente use 12pt. Detectados: 10pt",
        )

    def test_missing_abstract_includes_configured_word_range(self):
        violation = EumicViolationFactory.missing_abstract(
            min_words=100,
            max_words=300,
        )
        self.assertEqual(violation.category, EumicCategory.ABSTRACT_KEYWORDS)
        self.assertEqual(violation.severity, SeverityLevel.CRITICAL)
        self.assertEqual(
            violation.details,
            "El documento debe incluir un resumen de 100-300 palabras",
        )
        self.assertNotIn("150-250", violation.details)

    def test_missing_keywords_includes_configured_keyword_range(self):
        violation = EumicViolationFactory.missing_keywords(
            min_count=3,
            max_count=5,
        )
        self.assertEqual(violation.category, EumicCategory.ABSTRACT_KEYWORDS)
        self.assertEqual(violation.severity, SeverityLevel.CRITICAL)
        self.assertEqual(
            violation.details,
            "Se requieren 3-5 palabras clave relevantes al contenido",
        )
