from src.domain.dtos.eumic_violation_dto import EumicViolationDTO
from src.domain.enums.eumic_category import EumicCategory
from src.domain.enums.severity_level import SeverityLevel

_MAX_DISPLAYED_NON_STANDARD_SIZES: int = 3


class EumicViolationFactory:
    """Builds EumicViolationDTO instances for each EUMIC format check violation."""

    @staticmethod
    def margin_non_compliant(
        margin_name: str, actual_cm: float, required_cm: float
    ) -> EumicViolationDTO:
        return EumicViolationDTO(
            category=EumicCategory.FORMAT,
            message=f"Margen {margin_name} no cumple estándar EUMIC",
            severity=SeverityLevel.WARNING,
            details=f"Requerido: {required_cm} cm, Actual: {actual_cm:.2f} cm",
        )

    @staticmethod
    def non_standard_fonts(
        detected_fonts: set[str] | tuple[str, ...], allowed_fonts: tuple[str, ...]
    ) -> EumicViolationDTO:
        """Build violation for fonts outside the allowed fonts list."""
        return EumicViolationDTO(
            category=EumicCategory.FORMAT,
            message="Fuentes no estándar detectadas",
            severity=SeverityLevel.WARNING,
            details=f"Usar una de las fuentes permitidas: {', '.join(allowed_fonts)}. Detectadas: {', '.join(detected_fonts)}",
        )

    @staticmethod
    def variable_font_sizes(non_standard_sizes: list, required_size_pt: float) -> EumicViolationDTO:
        """Build violation for font sizes deviating from the required size."""
        sizes_str = ", ".join(
            f"{size.pt:.0f}pt" for size in non_standard_sizes[:_MAX_DISPLAYED_NON_STANDARD_SIZES]
        )
        return EumicViolationDTO(
            category=EumicCategory.FORMAT,
            message="Tamaños de fuente variables detectados",
            severity=SeverityLevel.INFO,
            details=f"Predominantemente use {required_size_pt:g}pt. Detectados: {sizes_str}",
        )

    @staticmethod
    def text_not_justified(non_justified: int, total: int) -> EumicViolationDTO:
        return EumicViolationDTO(
            category=EumicCategory.FORMAT,
            message="Texto no está completamente justificado",
            severity=SeverityLevel.WARNING,
            details=f"{non_justified}/{total} párrafos no justificados",
        )

    @staticmethod
    def figures_no_title(image_count: int) -> EumicViolationDTO:
        label = "imagen detectada" if image_count == 1 else "imágenes detectadas"
        return EumicViolationDTO(
            category=EumicCategory.FIGURES,
            message="Figuras sin título formal",
            severity=SeverityLevel.WARNING,
            details=f'{image_count} {label}. Se requiere formato "Figura 1. Título descriptivo" según normas APA',
        )

    @staticmethod
    def figures_inconsistent_numbering() -> EumicViolationDTO:
        return EumicViolationDTO(
            category=EumicCategory.FIGURES,
            message="Numeración de figuras inconsistente",
            severity=SeverityLevel.WARNING,
            details="Las figuras deben numerarse consecutivamente (Figura 1, Figura 2, ...)",
        )

    @staticmethod
    def tables_no_title(table_count: int, title_count: int) -> EumicViolationDTO:
        return EumicViolationDTO(
            category=EumicCategory.TABLES,
            message="Tablas sin título descriptivo",
            severity=SeverityLevel.WARNING,
            details=(
                f"{table_count} tablas detectadas, {title_count} títulos encontrados. "
                "Los títulos deben estar en la parte superior."
            ),
        )

    @staticmethod
    def tables_inconsistent_numbering() -> EumicViolationDTO:
        return EumicViolationDTO(
            category=EumicCategory.TABLES,
            message="Numeración de tablas inconsistente",
            severity=SeverityLevel.WARNING,
            details="Las tablas deben numerarse consecutivamente (Tabla 1, Tabla 2, ...)",
        )

    @staticmethod
    def formulas_not_centered(unaligned: int, total: int) -> EumicViolationDTO:
        return EumicViolationDTO(
            category=EumicCategory.FORMULAS,
            message="Fórmulas no centradas",
            severity=SeverityLevel.INFO,
            details=f"{unaligned}/{total} fórmulas no están centradas",
        )

    @staticmethod
    def missing_abstract(min_words: int, max_words: int) -> EumicViolationDTO:
        """Build violation for a missing abstract section."""
        return EumicViolationDTO(
            category=EumicCategory.ABSTRACT_KEYWORDS,
            message="Falta sección de Resumen/Abstract",
            severity=SeverityLevel.CRITICAL,
            details=f"El documento debe incluir un resumen de {min_words}-{max_words} palabras",
        )

    @staticmethod
    def abstract_length_out_of_range(
        word_count: int, min_words: int, max_words: int
    ) -> EumicViolationDTO:
        return EumicViolationDTO(
            category=EumicCategory.ABSTRACT_KEYWORDS,
            message="Extensión del resumen fuera de rango",
            severity=SeverityLevel.WARNING,
            details=f"Requerido: {min_words}-{max_words} palabras. Detectado: ~{word_count} palabras",
        )

    @staticmethod
    def missing_keywords(min_count: int, max_count: int) -> EumicViolationDTO:
        """Build violation for missing keywords section."""
        return EumicViolationDTO(
            category=EumicCategory.ABSTRACT_KEYWORDS,
            message="Faltan palabras clave",
            severity=SeverityLevel.CRITICAL,
            details=f"Se requieren {min_count}-{max_count} palabras clave relevantes al contenido",
        )

    @staticmethod
    def incorrect_keyword_count(count: int, min_count: int, max_count: int) -> EumicViolationDTO:
        return EumicViolationDTO(
            category=EumicCategory.ABSTRACT_KEYWORDS,
            message="Número incorrecto de palabras clave",
            severity=SeverityLevel.WARNING,
            details=f"Requerido: {min_count}-{max_count} palabras clave. Detectado: {count}",
        )
