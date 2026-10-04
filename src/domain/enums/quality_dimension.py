from enum import Enum


class QualityDimension(Enum):
    """The 4 semantic dimensions scored during quality analysis."""

    CLARITY = "claridad"
    COHERENCE = "coherencia"
    ARGUMENTATION = "argumentacion"
    CONCLUSIONS = "conclusiones"

    @property
    def label(self) -> str:
        """Return the Spanish display label for the quality dimension."""
        labels = {
            QualityDimension.CLARITY: "Claridad",
            QualityDimension.COHERENCE: "Coherencia",
            QualityDimension.ARGUMENTATION: "Argumentación",
            QualityDimension.CONCLUSIONS: "Conclusiones",
        }
        return labels[self]

    @classmethod
    def label_for(cls, key: str) -> str:
        """Return the Spanish display label for the given dimension key or capitalized fallback."""
        try:
            return cls(key).label
        except ValueError:
            return key.capitalize()
