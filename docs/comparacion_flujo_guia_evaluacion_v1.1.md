# Comparación del flujo: Guía de Evaluación v1.1 (punto 3) vs. estado actual

- **Documento base:** `2026-10-18_Silvina_Guia_Evaluacion_v1.1.docx`, sección 3 (Flujo de trabajo). Es un borrador en etapa de brainstorming.
- **Rama:** `silvina_editorial_v300` (parte de `silvina_editorial_v200`).
- **Alcance:** solo el flujo de etapas. No se comparan prompts, señales ni reglas de detalle. Las condiciones técnicas del punto 3.1 se tratan como configuración.

## Supuestos aclarados con el autor

- Los límites de caracteres de la Etapa 0 (5.000 y 35.000) son datos que se definirán por configuración.
- Las llamadas de calidad (Etapa 6) reciben el "texto completo sin bibliografía", igual que las de la Etapa 3.
- "Pasa a mérito" (Etapa 1, respaldo bibliográfico) se toma como "pasa a la siguiente etapa".

## Flujo actual

Definido en `AnalyzeDocumentUseCase._run_pipeline` (`src/application/analyze_document_use_case.py`):

1. Extraer contenido.
2. Validar largo máximo.
3. Extraer citas y referencias.
4. Validar APA.
5. Revisar gramática.
6. Clasificar el artículo.
7. Analizar calidad (incluye contribución y alineación).
8. Validar estructura según el tipo de artículo.
9. Cruzar citas con referencias.
10. Inspeccionar formato EUMIC.
11. Construir recomendaciones y veredicto.

## Comparación por etapa

| Etapa propuesta | Estado actual | Diferencia |
|---|---|---|
| **0. Admisión** (bloqueante: archivo legible, mínimo y máximo de caracteres) | Si el archivo no se puede leer o no se localiza el cuerpo, el análisis termina. El máximo (75.000, en `editorial_norms.toml`) se mide sobre título y cuerpo, sin bibliografía. | **Falta el mínimo.** Hoy no hay límite inferior. El máximo ya es configurable. |
| **1. Verificaciones formales** (gramática, APA, citas↔referencias, EUMIC) | Existen las cuatro verificaciones. Están repartidas antes y después de la clasificación y la calidad. | **Coincide en contenido.** Cambia el orden: hoy se intercalan con las etapas de LLM. |
| **1. Respaldo bibliográfico** (ex S2a/S2b, sale de la clasificación) | Es parte de la clasificación: S2a (cantidad de referencias) y S2b (referencias recientes) son señales de la tabla de reglas. `CitationCountRule` genera además una recomendación según la cantidad de citas. | **Difiere.** Hoy influye en el tipo de artículo. En la propuesta ya no. |
| **2. Señal determinística (C2)**: IMRyD o vocabulario metodológico | IMRyD completo decide **por sí solo** que el artículo es CIENTÍFICO y **saltea el LLM**. El vocabulario metodológico (S3) es otra señal de la tabla de reglas. | **Difiere.** En la propuesta ambos forman una sola señal que no decide por sí sola, y el LLM siempre corre. |
| **3. Señales LLM** (2 llamadas encadenadas: 1A pasa la cita del propósito a 1B) | 1 llamada con tres respuestas SI/NO (S4, S5, S6). Recibe el texto sin bibliografía. | **Difiere.** Hoy es 1 llamada y la propuesta son 2 en secuencia, con un dato que pasa de una a otra. El texto de entrada coincide. |
| **4. Clasificación** (R1, R2, R3) | Tabla de reglas ordenada en código (`ClassificationRuleTable`), de más de 15 filas: 4 científicas, unas 13 de divulgación y una de opinión como resto. | **Difiere en la forma.** Las tres categorías coinciden y Opinión es el residual en ambos. La propuesta pasa de una tabla a 3 reglas con confianza alta o media. |
| **5. Puerta de pertinencia** (pendiente) | No hay puerta. La alineación se calcula siempre, **después** de los puntajes de calidad. Solo aparece en el informe y no entra en el veredicto. | **Falta.** Hoy no corta nada y se evalúa más tarde. |
| **6. Calidad** (2 llamadas: Claridad+Coherencia y Argumentación+Conclusiones) | Mismas 2 llamadas con la misma agrupación, sobre texto sin bibliografía. Se suman 2 llamadas: contribución y alineación. | **Coincide en lo central.** Sobran las dos extra: la contribución se elimina y la alineación pasa a 1A. La escala hoy es 0–10 y en la propuesta es 1–5. |
| **7. Veredicto e informe** | Un evaluador por código (`PublicationVerdictEvaluator`) usa puntaje de calidad, gramática, estructura válida, coincidencia de citas y violaciones APA. Tiene tres estados: APTO, REQUIERE REVISIÓN, NO APTO. Además genera una lista de recomendaciones. | **Parcial.** El veredicto actual no usa la categoría ni la pertinencia. En el documento los umbrales están pendientes. |

## Llamadas al modelo

- **Actual:** hasta 5. Una de clasificación (ninguna si IMRyD está completo), dos de calidad y dos de idoneidad editorial (contribución y alineación).
- **Propuesto:** 4 en el caso normal, 2 si el documento no es pertinente.

## Presente en el sistema y ausente del flujo propuesto

- **Validación de estructura por categoría:** secciones requeridas según el tipo de artículo (`[required_sections]` en `editorial_norms.toml`). Se ejecuta después de la clasificación.
- **Clasificación de tamaño:** corto, largo o fuera de rango. Además condiciona el override por IMRyD.

## Preguntas abiertas

- ¿La validación de estructura por categoría y la clasificación de tamaño se omitieron del documento o se quieren eliminar?
