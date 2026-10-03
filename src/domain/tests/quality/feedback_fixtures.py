"""Condensed but structurally faithful fixtures of real LLM quality responses."""

FIXTURE_A_BULLET_SECTIONS_WEAKNESSES_SURVIVE = """## **1. Claridad del argumento** [Puntuación: 7/10]

**Fortalezas:**
- El mensaje central está bien definido: explicar los mecanismos de emergencia.
- Las tres preguntas de investigación actúan como brújula clara para el lector.
- La estructura de secciones es lógica y predecible a lo largo del manuscrito.

**Problemas de claridad:**
- La definición de emergencia es técnica y mezcla dos marcos sin separarlos.
- El resumen promete tres explicaciones pero no aclara cuál es más plausible.
- Los párrafos sobre BIG-Bench introducen evidencia sin conexión explícita.
- Párrafo adicional que debería descartarse por el límite de items por sección.
"""

FIXTURE_B_NESTED_NUMBERED_SUB_LIST = """## **1. Argumentación** [Puntuación: 8/10]

### Fortalezas
El texto presenta una estructura argumentativa sólida y multicapa:
- Problema bien delimitado en la introducción general.
- Tres hipótesis mecanicistas distinguibles y contrastables:
  1. Composición estadística de patrones textuales
  2. Andamiaje implícito de cadena de pensamiento
  3. Transiciones de fase representacionales
- Cuarto item descartable por exceder el tope de tres items principales.

### Debilidades
- Falta de síntesis conclusiva en el fragmento analizado.
- Conceptual slippage en la noción central de emergencia.
- Lacuna crítica sobre sensibilidad al formato del prompt.
"""

FIXTURE_C_HORIZONTAL_RULE_WITH_TABLE = """## **2. Conclusiones** [Puntuación: 6/10]

### Estado Actual
El texto no contiene una sección formal de conclusiones dentro del fragmento.

### Lo que Infiero del Contenido Final
1. No se descarta la complementariedad entre los mecanismos explicativos.
2. La evidencia empírica citada de interpretabilidad es aún preliminar.
3. Las preguntas iniciales de investigación permanecen sin resolución final.

---

### Síntesis Evaluativa

| Dimensión | Calificación | Justificación |
|-----------|-------------|---------------|
| Argumentación | 8/10 | Rigurosa |
| Conclusiones | 6/10 | Ausencia de cierre formal |

**Recomendación editorial**: Integrar los tres mecanismos en la discusión.
"""

FIXTURE_D_COHERENCIA_ELLIPSIS_ITEM = """## **2. Coherencia** [Puntuación: 7/10]

**Fortalezas:**
- El flujo general de la introducción es lógico y ordenado en su exposición.
- Las transiciones intraseccionales (ej: "En primer lugar... En segundo lugar... En tercer lugar") son claras y efectivas.
- La cita de referencia proporciona anclaje teórico consistente con el marco.
"""

FIXTURE_E_SAME_LEVEL_HEADING_ENDS_BLOCK = """## **1. Claridad** [Puntuación: 7/10]

**Fortalezas:**
- El objetivo general del estudio se formula de manera transparente.
- La secuencia temática facilita la comprensión global de los postulados.
- Las definiciones operativas se presentan con rigor terminológico adecuado.

## Observación final (meta)
Este párrafo de nivel dos no debe ser interpretado como parte de Claridad.
"""

FIXTURE_F_MID_SENTENCE_BOLD_STAYS_INLINE = """## **1. Claridad** [Puntuación: 8/10]

El texto mantiene una **claridad conceptual excelente** durante toda la exposición teórica del manuscrito.
"""

FIXTURE_G_MORE_THAN_THREE_ITEMS_SECTION = """## **1. Argumentación** [Puntuación: 8/10]

### Observaciones
- Primer argumento desarrollado con solvencia técnica y empírica comprobable.
- Segundo argumento respaldado por experimentos controlados en laboratorio.
- Tercer argumento fundamentado en literatura especializada del área temática.
- Cuarto argumento que excede la capacidad máxima de items del bloque.
- Quinto argumento complementario que también debe ser descartado del reporte.
"""

FIXTURE_H_GENERAL_SYNTHESIS_OVERWRITE_REGRESSION = """# Revisión Editorial Académica – Fragmento de Revisión Sistemática

## **1. Argumentación** [Puntuación: 8/10]

**Fortalezas:**

- **Estructura lógica clara**: El texto plantea tres preguntas interrelacionadas que dan coherencia.
- **Múltiples hipótesis contrastadas**: Se presentan tres explicaciones mecanicistas distintas sin favoritismo.
- **Evidencia empírica citada**: Se respaldan argumentos con trabajos específicos permitiendo verificabilidad.

**Debilidades:**

- **Desarrollo incompleto de hipótesis**: Cada mecanismo recibe tratamiento superficial en el texto.
- **Predicciones no siempre refutables**: La afirmación de emergencia necesita más detalle analítico.

---

## **2. Conclusiones** [Puntuación: 6/10]

**Análisis del párrafo final (Transiciones de fase representacionales):**

El texto **no cierra con conclusiones** sino que termina abruptamente en la hipótesis de transiciones:

- **Falta síntesis integradora**: No hay párrafo que reconcilie las tres hipótesis examinadas.
- **Ausencia de implicaciones articuladas**: No llega al análisis de implicaciones prometido.

**Lo que sí está presente:**

El párrafo final sí establece que la interpretabilidad mecanicista ha producido apoyo preliminar.

---

## Síntesis General

**Argumentación**: Sólida en presentación de alternativas teóricas, pero con desarrollos incompletos que restan profundidad (8/10).

**Conclusiones**: Ausentes o inconclusas. El texto termina en mitad de un argumento sin cerrar la discusión (6/10).

**Recomendación editorial**: Añadir un párrafo o sección de conclusiones que sintetice las hipótesis.
"""
