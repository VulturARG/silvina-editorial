from src.domain.classification.all_of_specification import AllOfSpecification
from src.domain.classification.has_evidence_based_contribution_specification import (
    HasEvidenceBasedContributionSpecification,
)
from src.domain.classification.has_methodological_vocabulary_specification import (
    HasMethodologicalVocabularySpecification,
)
from src.domain.classification.has_recent_references_specification import (
    HasRecentReferencesSpecification,
)
from src.domain.classification.has_research_intent_specification import (
    HasResearchIntentSpecification,
)
from src.domain.classification.has_sufficient_reference_count_specification import (
    HasSufficientReferenceCountSpecification,
)
from src.domain.classification.has_theoretical_justification_specification import (
    HasTheoreticalJustificationSpecification,
)
from src.domain.classification.rule_case import RuleCase
from src.domain.dtos.classification_signals_dto import ClassificationSignalsDTO
from src.domain.enums.article_type import ArticleType
from src.domain.enums.classification_confidence import ClassificationConfidence


class ClassificationRuleTable:
    """Ordered rule table mapping classification signals to an article type, confidence,
    and reasoning template. The last row is unconditional (legacy case 19, OPINION
    fallback) so evaluate() always returns a row — no separate fallback branch needed.
    """

    _FULL_CORE_SPECIFICATION = AllOfSpecification(
        HasMethodologicalVocabularySpecification(),
        HasResearchIntentSpecification(),
        HasEvidenceBasedContributionSpecification(),
    )

    _ROWS: tuple[RuleCase, ...] = (
        RuleCase(
            specification=AllOfSpecification(
                _FULL_CORE_SPECIFICATION,
                HasSufficientReferenceCountSpecification(),
                HasRecentReferencesSpecification(),
                HasTheoreticalJustificationSpecification(),
            ),
            article_type=ArticleType.SCIENTIFIC,
            confidence=ClassificationConfidence.FULL_SIGNAL_MATCH,
            reasoning_template=(
                "El artículo reúne la totalidad de los indicadores científicos: "
                "vocabulario metodológico (S3), intención investigativa (S4), "
                "contribución evidenciada (S5), justificación del marco teórico y "
                "vacío en la literatura (S6), cantidad de referencias suficiente (S2a) "
                "y bibliografía actualizada (S2b). Artículo científico con muy elevada "
                "confianza. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                _FULL_CORE_SPECIFICATION,
                HasRecentReferencesSpecification(),
                HasTheoreticalJustificationSpecification(),
            ),
            article_type=ArticleType.SCIENTIFIC,
            confidence=ClassificationConfidence.RECENT_BIBLIOGRAPHY_SUPPORT,
            reasoning_template=(
                "Vocabulario metodológico (S3), intención investigativa (S4), "
                "contribución evidenciada (S5) y justificación teórica (S6) presentes. "
                "Bibliografía reciente (S2b), aunque por debajo del umbral de cantidad "
                "mínima (S2a ausente). Artículo científico con confianza elevada. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                _FULL_CORE_SPECIFICATION,
                HasSufficientReferenceCountSpecification(),
                HasRecentReferencesSpecification(),
            ),
            article_type=ArticleType.SCIENTIFIC,
            confidence=ClassificationConfidence.COMPLETE_BIBLIOGRAPHY_SUPPORT,
            reasoning_template=(
                "Vocabulario metodológico (S3), intención investigativa (S4), "
                "contribución evidenciada (S5) y respaldo bibliográfico completo en "
                "cantidad y actualidad (S2a, S2b). No se detectó justificación del "
                "marco teórico ni identificación de vacío en la literatura (S6 ausente). "
                "Artículo científico de rigor metodológico; calificación de confianza "
                "media por ausencia de S6. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                _FULL_CORE_SPECIFICATION,
                HasSufficientReferenceCountSpecification(),
                HasTheoreticalJustificationSpecification(),
            ),
            article_type=ArticleType.SCIENTIFIC,
            confidence=ClassificationConfidence.SUFFICIENT_REFERENCE_COUNT,
            reasoning_template=(
                "Vocabulario metodológico (S3), intención investigativa (S4), "
                "contribución evidenciada (S5) y justificación teórica (S6) presentes. "
                "Cantidad de referencias suficiente (S2a). La bibliografía no alcanza "
                "el umbral de actualidad requerido (S2b ausente). Artículo científico "
                "de rigor metodológico; calificación de confianza media por ausencia "
                "de S2b. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                _FULL_CORE_SPECIFICATION, HasTheoreticalJustificationSpecification()
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "El artículo muestra indicadores cualitativos sólidos (S3, S4, S5, S6), "
                "pero carece del respaldo bibliográfico mínimo requerido "
                "(S2a y S2b ausentes). Revisión editorial recomendada: con la "
                "incorporación de respaldo bibliográfico suficiente en cantidad y "
                "actualidad, el artículo podría alcanzar el umbral para artículo "
                "científico. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                _FULL_CORE_SPECIFICATION, HasRecentReferencesSpecification()
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico, intención investigativa y contribución "
                "evidenciada presentes (S3, S4, S5), con bibliografía reciente (S2b). "
                "Sin justificación del marco teórico (S6) ni cantidad suficiente "
                "de referencias (S2a). Revisión editorial recomendada: con la "
                "incorporación de justificación del marco teórico (S6) y ampliación "
                "del número de referencias (S2a), el artículo podría alcanzar el "
                "umbral para artículo científico. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                _FULL_CORE_SPECIFICATION, HasSufficientReferenceCountSpecification()
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico, intención investigativa y contribución "
                "evidenciada presentes (S3, S4, S5), con cantidad de referencias "
                "suficiente (S2a). Sin justificación del marco teórico (S6) ni "
                "actualidad bibliográfica (S2b). Revisión editorial recomendada: con "
                "la incorporación de justificación del marco teórico (S6) y "
                "actualización de la bibliografía (S2b), el artículo podría alcanzar "
                "el umbral para artículo científico. "
            ),
        ),
        RuleCase(
            specification=_FULL_CORE_SPECIFICATION,
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico, intención investigativa y contribución "
                "evidenciada presentes (S3, S4, S5). Sin justificación del marco "
                "teórico (S6) ni respaldo bibliográfico (S2a, S2b). Las señales "
                "cualitativas sin soporte estructural son insuficientes para "
                "artículo científico. Revisión editorial recomendada: con la "
                "incorporación de justificación del marco teórico (S6) y "
                "fortalecimiento del respaldo bibliográfico en cantidad y actualidad "
                "(S2a, S2b), el artículo podría alcanzar el umbral para artículo "
                "científico. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                HasMethodologicalVocabularySpecification(), HasResearchIntentSpecification()
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico (S3) e intención investigativa (S4) presentes. "
                "No se detectó contribución basada en evidencia (S5 ausente). Sin los tres "
                "pilares cualitativos completos, la clasificación como artículo científico "
                "no es posible. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                HasMethodologicalVocabularySpecification(),
                HasEvidenceBasedContributionSpecification(),
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico (S3) y contribución basada en evidencia (S5) "
                "presentes. No se detectó intención investigativa explícita (S4 ausente). "
                "Sin los tres pilares cualitativos completos, la clasificación como "
                "artículo científico no es posible. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                HasMethodologicalVocabularySpecification(),
                HasSufficientReferenceCountSpecification(),
                HasRecentReferencesSpecification(),
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico (S3) y respaldo bibliográfico completo (S2a, S2b) "
                "presentes. No se detectaron intención investigativa (S4) ni contribución "
                "basada en evidencia (S5). Las señales cuantitativas sin pilares cualitativos "
                "son insuficientes para artículo científico. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                HasMethodologicalVocabularySpecification(),
                HasSufficientReferenceCountSpecification(),
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico (S3) y cantidad de referencias suficiente (S2a). "
                "Sin intención investigativa (S4), contribución evidenciada (S5) ni "
                "justificación teórica (S6). Evidencia insuficiente para artículo "
                "científico. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                HasMethodologicalVocabularySpecification(), HasRecentReferencesSpecification()
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico (S3) y bibliografía reciente (S2b). Sin intención "
                "investigativa (S4), contribución evidenciada (S5) ni justificación teórica "
                "(S6). Evidencia insuficiente para artículo científico. "
            ),
        ),
        RuleCase(
            specification=HasMethodologicalVocabularySpecification(),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Vocabulario metodológico presente (S3). Sin intención investigativa (S4), "
                "contribución evidenciada (S5), justificación teórica (S6) ni respaldo "
                "bibliográfico (S2a, S2b). El vocabulario técnico por sí solo es "
                "insuficiente para clasificar como artículo científico. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(
                HasResearchIntentSpecification(), HasEvidenceBasedContributionSpecification()
            ),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Intención investigativa (S4) y contribución evidenciada (S5) detectadas, "
                "pero sin vocabulario metodológico formal (S3 ausente). El artículo carece "
                "del sustento terminológico que distingue la investigación científica de la "
                "divulgación especializada. "
            ),
        ),
        RuleCase(
            specification=HasResearchIntentSpecification(),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Intención investigativa detectada (S4), pero sin vocabulario metodológico "
                "(S3), contribución evidenciada (S5) ni respaldo bibliográfico. La sola "
                "presencia de intención investigativa es insuficiente para artículo "
                "científico. "
            ),
        ),
        RuleCase(
            specification=HasEvidenceBasedContributionSpecification(),
            article_type=ArticleType.POPULAR_SCIENCE,
            confidence=None,
            reasoning_template=(
                "Contribución basada en evidencia detectada (S5), pero sin vocabulario "
                "metodológico (S3) ni intención investigativa (S4). Una contribución "
                "evidenciada sin proceso metodológico explícito no es suficiente para "
                "artículo científico. "
            ),
        ),
        RuleCase(
            specification=AllOfSpecification(),  # vacuously true (all([]) is True) — legacy
            # case 19 OPINION fallback, always matches if every row above did not
            article_type=ArticleType.OPINION,
            confidence=None,
            reasoning_template=(
                "No se detectaron señales de investigación científica ni de divulgación "
                "especializada. El artículo expone puntos de vista, argumentos o reflexiones "
                "sin respaldo metodológico ni evidencia sistemática. "
            ),
        ),
    )

    def evaluate(self, signals: ClassificationSignalsDTO) -> RuleCase:
        """Return the first matching rule case for the given signals.

        Always returns a row — the last row is unconditional (OPINION fallback).
        """
        for rule in self._ROWS:
            if rule.specification.is_satisfied_by(signals):
                return rule
        raise AssertionError("unreachable: the last row of _ROWS is unconditional")
