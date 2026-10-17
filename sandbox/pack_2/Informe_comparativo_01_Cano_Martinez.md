# Informe comparativo de modelos — `01_IMRyD_Cano_Martinez`

**Documento analizado:** J. J. Cano Martínez, *Prospectiva de ciberseguridad nacional para Colombia a 2030* (7.448 palabras, 18 tendencias Pestel).
**Fecha del informe:** 16/10/2026 · **Archivos comparados:** los 5 informes Word de `outputs/` (el JSON y el HTML se usaron solo para contrastar datos).
**Modelos:** Claude Haiku 4.5, Claude Haiku 5.5, Claude Sonnet 5.5, Claude Opus 5.5 y Gemma 4 26B (local, adaptado).

---

## 1. Conclusión

1. **Opus 5.5 es el más completo y fiable.** Detecta las 13 debilidades reales que identifiqué en el original y acierta la línea de investigación. Comete 2 errores menores.
2. **Sonnet 5.5 y Haiku 5.5 son buenas segundas opciones** (11,5 y 10,5 de 13). Sonnet es el más rápido (71,5 s). Haiku 5.5 señala con acierto que cuatro referencias aparecen por primera vez en la Conclusión, pero afirma que hay "quince tendencias" cuando hay 18.
3. **Haiku 4.5 queda a mitad de camino** (6,5 de 13): es correcto en lo general, pero inventa una cita textual y tiene dos transcripciones erróneas.
4. **Gemma 4 no es confiable para el juicio semántico.** Cubre 1 de las 13 debilidades, elogia justamente los puntos débiles del artículo (evidencia, Discusión) y su puntaje de 8,5 cambia el veredicto del informe a **"APTO PARA PUBLICACIÓN"**, cuando los otros cuatro dicen "REQUIERE REVISIÓN".
5. **Los cuatro modelos Claude afirman que la Tabla 1 "no aparece" y existe en el original.** Muy probablemente no sea un error de los modelos sino del pipeline: no encontré que el extractor de contenido pase las tablas al LLM (ver §5).

---

## 2. Alcance y método

- **Original usado:** `inputs/01_IMRyD_Cano_Martinez.docx`, versión actual. Ya no tiene "&" en las citas parentéticas y tiene la referencia provisional `Lastra, X. (2007)` (ver §8), por eso los 5 informes muestran 0 errores APA y 55/55 citas con referencia.
- **Verdad de referencia:** solo existe para la línea de investigación: `Verificacion lineas FMC.docx` indica **Científico con IMRyD, Línea 4**. Para el resto no hay verdad de referencia; verifiqué cada afirmación comprobable (citas textuales, conteos, ubicación de referencias) contra el texto del original.
- **Matriz de debilidades (§4):** armé la lista de 13 debilidades **después** de leer los 5 informes y comprobar cada una en el original. Mide cuánto cubre cada modelo de lo que, entre todos, se encontró; no es una lista cerrada ni independiente.
- **Tiempos y tokens:** tomados de `data/metrics.db` para la corrida que generó cada Word.
- **Limitación:** una sola corrida por modelo. La corrida previa de Haiku 4.5 (15:13) produjo un texto distinto con otros errores, así que el resultado varía de una corrida a otra.

---

## 3. Tabla comparativa

| Criterio | Haiku 4.5 | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 | Gemma 4 |
|---|---|---|---|---|---|
| **Puntaje general** | 6,5 | 5,5 | 6,0 | 6,0 | **8,5** |
| Claridad | 7 | 6 | 7 | 7 | 9 |
| Coherencia | 6 | 7 | 7 | 6 | 8 |
| Argumentación | 7 | 5 | 5 | 5 | 9 |
| Conclusiones | 6 | 4 | 5 | 6 | 8 |
| **Veredicto del Word** | Requiere revisión | Requiere revisión | Requiere revisión | Requiere revisión | **Apto para publicación** |
| Contribución | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| Alineación | ALINEADO | ALINEADO | ALINEADO | ALINEADO | ALINEADO |
| Líneas asignadas (ref.: **4**) | 4, 6, 7 ✗ | **4** ✓ | 4, 2, 6, 7 ✗ | **4** ✓ | 4, 6, 2 ✗ |
| **Cobertura de debilidades reales (de 13)** | 6,5 | 10,5 | 11,5 | **13** | 1 |
| Errores verificados en el texto | 3 | 3 | 2 | 2 | 0 (2 sobrevaloraciones) |
| Largo del Word (palabras) | 1.915 | 2.390 | 3.557 | 2.922 | 1.377 |
| Tiempo total del análisis | 82,7 s | 89,5 s | **71,5 s** | 113,2 s | 180,4 s |
| Tokens de entrada | 47.345 | 64.799 | 64.807 | 64.791 | 33.347 |
| Tokens de salida | 4.897 | 13.074 | 5.700 | 8.526 | 1.477 |
| Ejecución | API Anthropic | API Anthropic | API Anthropic | API Anthropic | Local (Ollama) |

Notas: no calculé costo en dinero porque el repositorio no contiene tarifas. Las diferencias en tokens de entrada (Haiku 4.5 y Gemma usan menos que los otros tres) pueden deberse al tokenizador de cada modelo; no lo verifiqué.

### Parte determinista (idéntica en los 5 Word)

| Elemento | Resultado | ¿Coincide con el original? |
|---|---|---|
| Clasificación | Científico, largo, IMRyD completo | ✓ (coincide con la verificación manual) |
| Palabras / caracteres | 7.448 / 51.013 | ✓ (7.219 de cuerpo + 229 de la tabla) |
| Gramática | 7,0/10, 9 errores (se muestran 5 y el aviso "Solo se muestran los primeros 5 errores detectados.") | ✓ |
| APA 7 | Sin errores | ✓ (el original ya usa "y") |
| Citas | 55 citas, 55 referencias, 100 % de coincidencia | ✓ |
| Estructura EUMIC | Válida | ✓ |
| Norma EUMIC no cumplida | Fuente de 10 pt (tabla y pie de tabla) | ✓ (único texto fuera de 12 pt) |

---

## 4. Cobertura de debilidades reales del artículo

✓ la señala · ◐ la señala en parte · ✗ no la señala. Cada debilidad fue comprobada en el original.

| # | Debilidad (verificada en el original) | Haiku 4.5 | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 | Gemma 4 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| 1 | Poca dimensión prospectiva: sin escenarios, sin priorización de las 18 tendencias | ✓ | ✓ | ✓ | ✓ | ✗ |
| 2 | Evidencia basada en prensa, sin datos cuantitativos | ✓ | ✓ | ✓ | ✓ | ✗ |
| 3 | Metodología sin número ni perfil de los entrevistados | ✗ | ✓ | ✓ | ✓ | ✗ |
| 4 | Referencias que aparecen por primera vez en la Conclusión (Alcolea, Singer y Brooking, Hoffman y Levite, Dash, McNulty, Téllez, Fergnani, Wolfowitz) | ✗ | ✓ | ◐ | ✓ | ✗ |
| 5 | Solapamiento entre tendencias políticas y sociales | ✓ | ✓ | ✓ | ✓ | ✗ |
| 6 | Atribución a "agentes extranjeros / no estatales" sin sustento | ✗ | ✓ | ✓ | ✓ | ✗ |
| 7 | Tendencias o rótulos que no corresponden a su contenido (p. ej. "Regulaciones vigentes", "Patrocinio de ataques") | ◐ | ◐ | ✓ | ✓ | ✗ |
| 8 | Ejemplos de Afganistán y EE. UU. sin conexión con Colombia | ✓ | ✓ | ✓ | ✓ | ✗ (los elogia) |
| 9 | "Los resultados confirman los eventos": razonamiento invertido | ✗ | ✓ | ✓ | ✓ | ✗ |
| 10 | Conclusión genérica: sin acciones, responsables ni indicadores | ✓ | ✓ | ✓ | ✓ | ◐ |
| 11 | Dimensión ecológica débilmente conectada con la ciberseguridad | ✓ | ✓ | ✓ | ✓ | ◐ |
| 12 | "CO" en lugar de "CO₂" en el texto original | ✗ | ✗ | ✗ | ✓ | ✗ |
| 13 | Lastra (2007) como respaldo de un movimiento empresarial actual (anacrónico) | ✗ | ✗ | ✓ | ✓ | ✗ |
| | **Total** | **6,5** | **10,5** | **11,5** | **13** | **1** |

### Aportes exclusivos

- **Opus:** único que señala "CO" en vez de CO₂ (#12). Es también el único con la lista completa de ocho referencias que aparecen solo en la Conclusión.
- **Sonnet:** único que señala el uso de Deloitte (2019) para describir efectos de la pandemia (cronológicamente problemático).
- **Haiku 5.5:** señala que Alcolea, Singer y Brooking, Hoffman y Levite y Dash se citan solo en la Conclusión (se confirma en el original). Junto con Opus, es el único que asigna la línea 4 como única.
- **Gemma:** única virtud: es el modelo más económico en tokens y corre local.

---

## 5. Errores verificados contra el original

### Haiku 4.5 (3)
- Cita "**eventualmente afectarán...**" como frase del texto: **no existe** (la palabra "eventual..." no aparece en el artículo).
- Escribe "**Infobea**" donde el original dice "Infobae".
- Cita "Gafam generan **CO2**..." (el original escribe "CO", sin 2).
- Además: califica la Argumentación con 7/10 pero enumera cinco "debilidades críticas".

### Haiku 5.5 (3)
- Dice "**quince tendencias**": son **18** (3 × 6).
- Afirma que la **Tabla 1 no aparece**: está en el original.
- Dice que la cifra de las Gafam "no tiene referencia suficiente": **sí la tiene** (Nogueira, 2020).

### Sonnet 5.5 (2)
- Afirma que la Tabla 1 "aparece sin contenido": tiene contenido en el original.
- Atribuye a la Conclusión la estrategia "no estandarizada": está en la **Discusión**.

### Opus 5.5 (2)
- Dice que la **Tabla 1** "no aparece en el fragmento".
- Afirma que la Introducción se apoya en Singer y Brooking y en Buchanan: Singer solo se cita en la Conclusión y Buchanan aparece en Resultados.

### Gemma 4 (0 errores textuales, 2 sobrevaloraciones)
- Afirma que el autor respalda **cada afirmación con evidencias empíricas**: en las dimensiones legal y ecológica las "evidencias" son enumeraciones breves sin fuente (por ejemplo, "Hay una creciente transformación digital...").
- Elogia la Discusión (Afganistán, EE. UU.), cuando los cuatro modelos Claude la señalan como un salto argumentativo sin conexión con Colombia.

> **Sobre la Tabla 1:** en el código, solo `docx_eumic_adapter.py` lee las tablas del documento; no encontré extracción de tablas en el adaptador que arma el texto para el LLM. Es la explicación más probable de que todos los Claude digan que la Tabla 1 falta, y de que Gemma no la mencione.

---

## 6. Hallazgos sobre el producto (no sobre los modelos)

1. **El veredicto depende del modelo.** Con `publish_threshold = 7,0`, Gemma (8,5) deja el documento "APTO PARA PUBLICACIÓN" y todos los Claude (≤ 6,5) "REQUIERE REVISIÓN". Con un modelo que sobrevalora, el sistema aprobaría un artículo con contribución PARCIAL y debilidades que los cuatro modelos Claude documentan.
2. **El Word de Gemma se contradice.** Dice que el documento "cumple con todos los estándares de calidad, estructura y formato APA 7 requeridos por las normas EUMIC", y más abajo lista "Normas editoriales no cumplidas (EUMIC)" por la fuente de 10 pt.
3. **La Tabla 1 no llega al modelo** (ver §5): las críticas "la tabla no aparece" son un falso negativo del pipeline.
4. **Campos truncados con "…"**: "Aporte identificado", "Justificación" y las líneas de investigación terminan a mitad de frase en los 5 Word.
5. **Líneas de investigación:** cada modelo las devuelve en un formato distinto (solo números en Haiku 4.5; número con descripción larga en Haiku 5.5, Opus y Sonnet).
6. **Variabilidad entre corridas:** Haiku 4.5 produjo contenido y errores distintos en dos corridas con puntaje idéntico (6,5). Un puntaje único no es estable.

---

## 7. Recomendaciones

1. **Usar Opus 5.5 o Sonnet 5.5** para la evaluación semántica. Si el costo importa, Sonnet es el mejor equilibrio (11,5 de 13 y el más rápido).
2. **No usar Gemma 4 para el veredicto.** Si se mantiene para uso local, no debería poder dejar "APTO PARA PUBLICACIÓN" sin verificación humana.
3. **Pasar las tablas al LLM** para evitar falsos negativos como el de la Tabla 1.
4. **Normalizar el formato de las líneas de investigación** y no truncar con "…" los campos de Pertinencia Editorial.
5. **Repetir cada modelo al menos 2–3 veces** antes de concluir, dado que Haiku 4.5 cambió de contenido entre corridas.

---

## 8. Notas

- El original de `pack_2` fue editado entre las corridas iniciales y estas (se reemplazaron los "&" por "y" y se ajustaron comas). Esas ediciones, junto con la referencia provisional de Lastra, quedaron en el commit `5dc1a27` del PR #109, que yo describí como "solo agrega la referencia". Si no querías esos cambios en el repositorio, hay que revertirlos.
- La entrada `Lastra, X. (2007). [Título pendiente].` es un dato inventado a pedido del usuario para eliminar el error de cita huérfana; debe reemplazarse por la fuente real.
