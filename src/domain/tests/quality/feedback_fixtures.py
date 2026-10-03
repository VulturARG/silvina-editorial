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
- Cuarto aspecto que ahora sobrevive con el nuevo tope de ocho items.
- Quinto aspecto que también sobrevive con el nuevo tope de ocho items.
- Sexto aspecto analítico sobre la delimitación empírica del problema.
- Séptimo aspecto sobre los umbrales de escala y su validez externa.
- Octavo aspecto sobre la integración formal de las definiciones previas.
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
- Tercer aspecto relevante sobre la formulación analítica de supuestos.
- Cuarto aspecto válido sobre el diseño experimental del estudio.
- Quinto aspecto válido sobre la consistencia empírica observada.
- Sexto aspecto sobre la validez del marco metodológico empleado.
- Séptimo aspecto sobre la replicabilidad de las pruebas empíricas.
- Octavo aspecto sobre la exhaustividad del relevamiento bibliográfico.
- Noveno item descartable por exceder el tope de ocho items principales.

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

FIXTURE_G_MORE_THAN_FIVE_ITEMS_SECTION = """## **1. Argumentación** [Puntuación: 8/10]

### Observaciones
- Primer argumento desarrollado con solvencia técnica y empírica comprobable.
- Segundo argumento respaldado por experimentos controlados en laboratorio.
- Tercer argumento fundamentado en literatura especializada del área temática.
- Cuarto argumento que demuestra consistencia analítica en el desarrollo.
- Quinto argumento que cierra el bloque principal de observaciones válidas.
- Sexto argumento que excede la capacidad máxima de cinco items del bloque.
- Séptimo argumento complementario que también debe ser descartado del reporte.
"""

FIXTURE_G_MORE_THAN_EIGHT_ITEMS_SECTION = """## **1. Argumentación** [Puntuación: 8/10]

### Observaciones
- Primer argumento desarrollado con solvencia técnica y empírica comprobable.
- Segundo argumento respaldado por experimentos controlados en laboratorio.
- Tercer argumento fundamentado en literatura especializada del área temática.
- Cuarto argumento que demuestra consistencia analítica en el desarrollo.
- Quinto argumento que consolida la base explicativa del marco teórico.
- Sexto argumento con formulación cuantitativa precisa de las variables.
- Séptimo argumento apoyado en réplicas independientes de la literatura.
- Octavo argumento que cierra el bloque principal de observaciones válidas.
- Noveno argumento que excede la capacidad máxima de ocho items del bloque.
- Décimo argumento complementario que también debe ser descartado del reporte.
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

FIXTURE_I_SONNET_STYLE_PLAIN_TITLES = """## **1. Claridad** [Puntuación: 8/10]

El argumento central se entiende con facilidad en toda la exposición teórica.

Lo que funciona bien:
- Primera fortaleza bien formulada en el manuscrito.
- Segunda fortaleza con delimitación conceptual clara.
- Tercera fortaleza apoyada en preguntas de investigación.
- Cuarta fortaleza con síntesis de mecanismos explicativos.

Lo que necesita mejorar:
- Primer aspecto débil que requiere mayor precisión terminológica.
- Segundo aspecto débil sobre los umbrales numéricos de escala.
- Tercer aspecto débil sobre criterios de inclusión del corpus.
- Cuarto aspecto débil en la transición lógica entre secciones.
- Quinto aspecto débil sobre la justificación metodológica.
- Sexto aspecto débil sobre la discusión de limitaciones empíricas.
- Séptimo aspecto débil sobre el marco comparativo de referencia.
- Octavo aspecto débil sobre la consistencia en la notación formal.
- Noveno aspecto débil descartado por exceder el tope de ocho items.
"""

FIXTURE_J_HAIKU_ID_60_PARAGRAPH_FLUSH_BULLETS = """## **1. Argumentación** [Puntuación: 8/10]

### Fortalezas

**Estructura lógica clara**: El texto presenta tres preguntas de investigación interrelacionadas en la introducción.

**Síntesis tripartita de explicaciones mecanicistas**: Los autores presentan tres hipótesis competentes sin privilegiar arbitrariamente una:
- Composición estadística parsimoniosa pero insuficiente para BIG-Bench
- Andamiaje implícito de cadena de pensamiento sensible al contexto
- Transiciones de fase representacionales con evidencia de interpretabilidad

Cada una se presenta con su base empírica y limitaciones, lo que muestra pensamiento crítico.

**Identificación de tensiones teóricas**: El texto reconoce explícitamente la insuficiencia de una perspectiva puramente estadística.
"""

FIXTURE_K_GEMMA_STYLE_PLAIN_WEAKNESS_TITLE = """## **1. Claridad** [Puntuación: 9/10]

El argumento central es extremadamente claro y está bien estructurado desde el inicio.

Lo que funciona muy bien:
- La delimitación del problema es excelente desde el resumen inicial.
- La división de las explicaciones teóricas permite categorizar la información.

Lo que podría mejorar:
- La transición hacia las transiciones de fase se siente más abstracta que las anteriores.
"""

FIXTURE_L_PLAIN_FORTALEZAS_DEBILIDADES_TITLES = """## **1. Argumentación** [Puntuación: 7/10]

El texto presenta una estructura argumentativa clara y organizada en hipótesis rivales.

Fortalezas:
- Primera fortaleza metodológica relevante en el desarrollo.
- Segunda fortaleza analítica bien fundamentada con datos.

Debilidades:
- Primera debilidad en la integración conceptual de las hipótesis.
- Segunda debilidad sobre el alcance temporal de la muestra.
"""

FIXTURE_M_OPUS_ID_70_PARAGRAPH_FLUSH_BULLETS_WITH_SUB_BULLETS = """## **1. Argumentación** [Puntuación: 6/10]

El texto tiene una estructura argumentativa clara. Plantea tres preguntas de investigación, organiza el marco teórico en tres hipótesis y presenta para cada una evidencia a favor y algunas objeciones. Sin embargo, varios problemas de contenido debilitan la solidez:

- **Contradicción numérica sin resolver.** El Resumen afirma que las capacidades emergentes son detectables a partir de 10^9 parámetros.
- **Citas que no respaldan lo que se les atribuye:**
  - Bai et al. (2022), el trabajo de IA constitucional, trata sobre alineación mediante retroalimentación de IA.
  - Lanham et al. (2023) estudia la fidelidad del razonamiento en cadena de pensamiento.
  - Mitchell (2021) es un ensayo crítico sobre las limitaciones de la IA.
  - Power et al. (2022), sobre grokking, describe transiciones en función del tiempo de entrenamiento.
  - El cambio de fase asociado a la adquisición de circuitos se documenta en Olsson et al.
- **Salto inferencial.** Que el desempeño humano esté por encima del azar no implica que las tareas no puedan adquirirse.
- **Afirmaciones sin sustento:**
  - El mecanismo de cabezas de atención como circuitos se presenta sin cita.
  - Decir que la predicción de la cadena de pensamiento se confirma es una afirmación excesiva.
- **Debilidad metodológica de la revisión sistemática.** Se mencionan las bases de datos pero faltan criterios de inclusión.
- **Falta de contraste entre hipótesis.** Las tres explicaciones se presentan como alternativas sin contrastarlas.
"""
