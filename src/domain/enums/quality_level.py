from enum import Enum

from src.domain.dtos.quality_level_thresholds_dto import QualityLevelThresholdsDTO


class QualityLevel(Enum):
    """Quality levels for article assessment."""

    EXCELLENT = "Excelente"
    GOOD = "Bueno"
    ACCEPTABLE = "Aceptable"
    NEEDS_IMPROVEMENT = "Requiere mejoras"
    POOR = "Deficiente"

    @classmethod
    def from_score(cls, score: float, thresholds: QualityLevelThresholdsDTO) -> "QualityLevel":
        """Map an overall quality score to the highest level whose threshold it reaches."""
        if score >= thresholds.excellent_threshold:
            return cls.EXCELLENT
        if score >= thresholds.good_threshold:
            return cls.GOOD
        if score >= thresholds.acceptable_threshold:
            return cls.ACCEPTABLE
        if score >= thresholds.needs_improvement_threshold:
            return cls.NEEDS_IMPROVEMENT
        return cls.POOR
