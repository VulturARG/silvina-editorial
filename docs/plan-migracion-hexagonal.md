# Plan de Migración a Arquitectura Hexagonal — Silvina Editorial Assistant

> Documento de estudio. **No implementa cambios.** Define el camino desde la
> arquitectura por capas actual hacia la arquitectura hexagonal cuyo esqueleto
> ya está definido en `src/`.
>
> Guía normativa de implementación: `.agent/skills/clean-architecture/SKILL.md`
> (a usar en la etapa posterior de implementación).
>
> Estrategia acordada: **incremental por slices verticales**, código viejo y
> `src/` **coexisten** hasta terminar cada slice. Entry points (`main.py`,
> `gradio_app.py`) quedan **en la raíz** como driving adapters. Tests se
> **reescriben** como `unittest.TestCase` dentro de `src/`. Alcance: **todo el
> sistema actual**.

---

## 1. Resumen ejecutivo

La aplicación ya está organizada en capas (`domain`, `data_access`,
`business_logic`, `presentation`) más entry points en la raíz. Es un buen punto
de partida: la dirección de dependencias es casi correcta, pero hay tres
problemas que la arquitectura hexagonal resuelve:

1. **No hay inversión de dependencias.** La lógica de negocio importa
   directamente librerías de infraestructura (`ollama`, `language_tool_python`,
   `docx`). No hay puertos (interfaces) que aíslen el dominio del mundo exterior.
2. **No hay cableado explícito (wiring).** Las dependencias se instancian dentro
   de `SilvinaEditorialAssistant.__init__` y dentro de los propios servicios,
   mezclando construcción con ejecución.
3. **El "dominio" actual mezcla datos puros con I/O.** `data_access` y partes de
   `business_logic` son en realidad **adapters**, no dominio.

El destino hexagonal separa tres anillos:

- **`src/domain/`** — entidades, DTOs, enums, excepciones, servicios de dominio
  y **puertos** (interfaces). Cero dependencias de frameworks.
- **`src/application/`** — casos de uso. Orquestan dominio. Dependen solo de
  `src/domain/`.
- **`src/infrastructure/`** — adapters (implementan los puertos sobre `docx`,
  `ollama`, `win32com`, `language_tool`), wirings y tests de integración.

**Dato clave: este sistema NO tiene base de datos.** Por lo tanto, según el
SKILL (§4), **todos los puertos llevan sufijo `Port`** (interacción externa
no-DB). No habrá ninguna clase `Repository`.

---

## 2. Estado actual (línea de base)

### 2.1 Estructura de carpetas (código a migrar)

```
domain/            # Datos + helpers (casi puro)
  models.py        # 12 @dataclass: Citation, Reference, DocumentContent, Section,
                   #   ClassificationResult, QualityResult, StructureValidationResult,
                   #   CitationAnalysisResult, QualityAnalysisResult, AnalysisResult...
  enums.py         # 9 Enum + helpers (classify_article_size, classify_section_by_name...)

data_access/       # TODO esto es infraestructura (I/O de archivos Word)
  word_reader.py        # python-docx: lee párrafos
  content_extractor.py  # extrae título/autores/abstract/secciones de párrafos
  citation_parser.py    # python-docx XML: extrae citas y notas al pie
  reference_parser.py   # python-docx XML: extrae bibliografía
  word_counter.py       # win32com (Word COM): conteo exacto de caracteres

business_logic/    # Casos de uso + servicios de dominio (con fugas de infra)
  article_classifier.py # Ollama (LLM) + reglas → ClassificationResult
  quality_analyzer.py   # Ollama (LLM) → QualityResult
  structure_validator.py# Puro: valida secciones requeridas
  structure_analyzer.py # Puro: detecta secciones presentes
  citation_matcher.py   # Casi puro: relaciona citas↔referencias (toca docx en 1 método)
  gramatica_checker.py  # language_tool_python: gramática/ortografía
  article_analyzer.py   # Orquestador alternativo (parcialmente duplicado de main.py)
  vocab/methodological_terms.py  # Datos (vocabulario)

presentation/      # Mezcla: formateo puro + export docx + config
  report_formatter.py   # Puro: arma reporte de texto
  word_exporter.py      # python-docx: exporta reporte a .docx
  config.py             # Configuración (Ollama URL, modelo, secciones requeridas)

# Raíz (entry points + validadores sueltos)
main.py            # Controller CLI + orquestador SilvinaEditorialAssistant
gradio_app.py      # Controller Web (Gradio)
apa_validator.py   # Puro: valida formato APA 7 de citas
eumic_verifier.py  # python-docx: verifica normas de formato EUMIC
process_feedback.py# Script: procesa feedback de expertos
config.py          # Config raíz (REQUIRED_SECTIONS, etc.)
conftest.py        # pytest

tests/             # Suite pytest actual (red de seguridad temporal)
```

### 2.2 Mapa de dependencias externas (definen los adapters)

| Librería externa | Usada por | Frontera (futuro puerto) |
|---|---|---|
| `ollama` | `article_classifier`, `quality_analyzer` | `LanguageModelPort` |
| `python-docx` | `word_reader`, `content_extractor`, `citation_parser`, `reference_parser`, `word_exporter`, `eumic_verifier`, `citation_matcher` | varios puertos de documento |
| `win32com` (Word COM) | `word_counter` | `CharacterCountPort` |
| `language_tool_python` | `gramatica_checker` | `GrammarCheckPort` |
| `gradio` | `gradio_app` | driving adapter (raíz) |

### 2.3 Diagnóstico de la dirección de dependencias actual

```
main.py ──> business_logic ──> data_access ──> domain
   │             │  (ollama,        (docx,        (puro)
   │             │   lang_tool)      win32)
   └──> presentation (docx export, config)
```

- ✅ `domain` no importa nada hacia afuera (correcto).
- ⚠️ `business_logic` importa `data_access` (`article_analyzer`) y librerías de
  infraestructura directamente → **violación de inversión de dependencias**.
- ⚠️ `business_logic.structure_validator` importa `config` (raíz) →
  acoplamiento a configuración concreta.
- ⚠️ Imports locales dentro de funciones (`from apa_validator import ...` dentro
  de `analyze_document`) → el SKILL §3 los prohíbe.

---

## 3. Arquitectura destino (hexagonal)

### 3.1 La estructura de `src/` NO cambia

El esqueleto existente se respeta tal cual. Solo se **rellena**:

```
src/
├── domain/
│   ├── entities/        # base_entity.py (ya existe) + entidades migradas
│   ├── enums/           # enums migrados
│   ├── dtos/            # base_dto.py (ya existe) + DTOs migrados
│   ├── exceptions/      # base_src_error.py (ya existe) + <grupo>_errors.py
│   │   └── decorators/  # generic_error_handler.py (ya existe)
│   ├── tests/           # tests unittest de dominio
│   └── <entity_name>/   # carpeta por entidad: servicios de dominio + PUERTOS
├── application/         # casos de uso (UseCase)
└── infrastructure/
    ├── adapters/<entity_name>/   # adapters que implementan los puertos
    ├── wirings/                  # ensamblado por caso de uso
    └── tests/test_doubles/       # wirings y dobles de prueba
```

**Regla de oro (SKILL §1):** no existen carpetas `services/` ni `ports/` de
primer nivel. Los puertos y servicios viven **dentro de la carpeta de su
entidad** en `domain/`, solo cuando se necesitan.

### 3.2 Dónde vive cada cosa (entry points fuera de `src/`)

```
                 DRIVING (entrada)                         DRIVEN (salida)
   ┌──────────────────────────────┐         ┌──────────────────────────────────┐
   │  main.py        (raíz, CLI)  │         │  Ollama / python-docx / win32com  │
   │  gradio_app.py  (raíz, Web)  │         │  language_tool                     │
   └───────────────┬──────────────┘         └────────────────▲─────────────────┘
                   │ arma wiring e invoca                      │ implementan puertos
                   ▼                                           │
           src/infrastructure/wirings  ──crea──►  src/infrastructure/adapters
                   │                                           │
                   ▼ inyecta                                   │
           src/application (UseCases) ──depende──► src/domain (entidades, puertos)
```

`main.py` y `gradio_app.py` quedan en la raíz: **solo** construyen el wiring del
caso de uso y muestran resultados. No contienen lógica de negocio.

---

## 4. Mapa maestro de migración (origen → destino)

> `<entity>` = nombre de carpeta de entidad en `domain/` e `infrastructure/adapters/`.

### 4.1 Dominio puro (datos)

| Origen | Destino | Tipo destino |
|---|---|---|
| `domain/enums.py` (los `Enum`) | `src/domain/enums/<uno por archivo>.py` | enum |
| `domain/models.py::Citation` | `src/domain/citation/citation.py` | Entity (`BaseEntity`) |
| `domain/models.py::Reference` | `src/domain/reference/reference.py` | Entity |
| `domain/models.py::Section` | `src/domain/section/section.py` | Entity |
| `domain/models.py::DocumentContent` | `src/domain/document/document_content.py` | Entity (tiene `__post_init__`) |
| `domain/models.py::ClassificationResult` | `src/domain/dtos/classification_result_dto.py` | DTO (`BaseDTO`, inmutable) |
| `domain/models.py::QualityResult` | `src/domain/dtos/quality_result_dto.py` | DTO |
| `domain/models.py::StructureValidationResult` | `src/domain/dtos/structure_validation_result_dto.py` | DTO |
| `domain/models.py::CitationAnalysisResult` | `src/domain/dtos/citation_analysis_result_dto.py` | DTO |
| `domain/models.py::AnalysisResult` | `src/domain/dtos/analysis_result_dto.py` | DTO (agregado de salida) |

> **Decisión a confirmar en implementación:** Entity vs DTO. Criterio del SKILL:
> Entity = mutable, tiene comportamiento (`BaseEntity` + `@dataclass`); DTO =
> inmutable (`@dataclass(frozen=True)`, `BaseDTO`), cruza fronteras. Los
> "*Result" son datos de salida inmutables → DTO. Los modelos con
> comportamiento/mutación (`DocumentContent`, `Citation`...) → Entity.

> **Limpieza pendiente en `models.py`:** hay duplicación (`QualityResult` vs
> `QualityAnalysisResult`), helpers rotos (`create_classification_result` pasa
> `category=` a un dataclass cuyo campo es `article_type`) y un `__all__` en
> `enums.py` que lista `SeverityLevel` antes de definirlo. La migración es la
> oportunidad para consolidar; cada caso se decide en su slice.

### 4.2 Funciones sueltas → clases (POO total)

**Convención del proyecto (incorporada al SKILL §4):** todo es POO.
**No quedan funciones de módulo en el dominio.** El SKILL §4 ahora exige **una
clase o función por archivo** y prefiere POO: la lógica de dominio se modela como
clases, no como funciones de módulo. Una función sola en su archivo se reserva
para artefactos que son genuinamente funciones (ej. el decorador
`generic_error_handler`). Así "un artefacto por archivo" aplica de forma universal
(única excepción: `domain/exceptions/`).

Cada helper actual se transforma en una **clase de servicio de dominio** (nombre
descriptivo, sin sufijo `Service` — SKILL §4) con un método público, y vive en
**su propio archivo** dentro de la carpeta de su entidad.

| Función suelta actual (`enums.py`) | Clase destino (1 por archivo) | Método público | Carpeta |
|---|---|---|---|
| `classify_article_size(char_count)` | `ArticleSizeClassifier` | `classify(char_count) -> ArticleSize` | `domain/article/` |
| `get_quality_level_from_score(score)` | `QualityLevelResolver` | `resolve(score) -> QualityLevel` | `domain/quality/` |
| `classify_section_by_name(name)` | `SectionClassifier` | `classify(name) -> SectionType` | `domain/section/` |
| `get_required_sections_for_category(cat)` | `RequiredSectionsProvider` | `for_category(cat) -> list[SectionType]` | `domain/structure/` |
| `get_citation_type_from_pattern(text)` | `CitationTypeDetector` | `detect(text) -> CitationType` | `domain/citation/` |

**Helpers de creación de `models.py`** (`create_empty_document`,
`create_classification_result`, `create_quality_result`): NO se vuelven clases
sueltas. Se modelan como **`@classmethod` factory** en la propia entidad/DTO
(ej. `DocumentContent.empty()`), o se **eliminan** si están rotos (varios lo
están — ver §4.1). Esto es POO y respeta una clase por archivo.

**Funciones sueltas fuera del dominio** (fachadas de conveniencia como
`validate_apa_citations`, `verify_eumic_compliance`, `read_word_file`,
`classify_document`, `analyze_structure`, `check_gramatica`): al migrar
desaparecen o se vuelven **métodos** de su adapter / caso de uso correspondiente.
Ninguna sobrevive como función de módulo.

### 4.3 Adapters (lo que hoy es `data_access` + I/O de `presentation`)

| Origen | Puerto (en `domain/<entity>/`) | Adapter (en `infrastructure/adapters/<entity>/`) | Backend |
|---|---|---|---|
| `word_reader.py` | `DocumentTextPort` | `DocxTextAdapter` | python-docx |
| `content_extractor.py` | `ContentExtractionPort` | `ParagraphContentAdapter` | python-docx (heurísticas) |
| `citation_parser.py` | `CitationExtractionPort` | `DocxCitationAdapter` | python-docx XML |
| `reference_parser.py` | `ReferenceExtractionPort` | `DocxReferenceAdapter` | python-docx XML |
| `word_counter.py` | `CharacterCountPort` | `Win32ComWordCountAdapter` | win32com |
| `word_exporter.py` | `ReportExportPort` | `DocxReportAdapter` | python-docx |
| `eumic_verifier.py` | `DocumentFormatInspectionPort` | `DocxEumicAdapter` | python-docx |

> **Decisión de granularidad (ISP):** puertos **enfocados** (uno por capacidad),
> aunque varios adapters compartan `python-docx` por debajo. Esto mantiene los
> casos de uso dependiendo solo de lo que usan. Alternativa descartada: un único
> `DocumentPort` gordo (rompe Interface Segregation).

### 4.4 Servicios de dominio + casos de uso (lo que hoy es `business_logic`)

| Origen | Naturaleza | Destino |
|---|---|---|
| `article_classifier.py` | LLM + reglas | servicio `ArticleClassifier` en `domain/article/` (reglas puras) + use case `ClassifyArticleUseCase` que usa `LanguageModelPort` |
| `quality_analyzer.py` | LLM | `AnalyzeQualityUseCase` (usa `LanguageModelPort`) |
| `structure_validator.py` | puro | servicio `StructureValidator` en `domain/structure/` + `ValidateStructureUseCase` |
| `structure_analyzer.py` | puro | servicio `domain/structure/` (fusionar con validator) |
| `citation_matcher.py` | casi puro | servicio `CitationMatcher` en `domain/citation/` + `MatchCitationsUseCase` |
| `gramatica_checker.py` | language_tool | `CheckGrammarUseCase` (usa `GrammarCheckPort`) |
| `apa_validator.py` (raíz) | puro | servicio `ApaValidator` en `domain/citation/` + `ValidateApaUseCase` |
| `article_analyzer.py` | orquestador duplicado | **descartar**; su rol lo cumple el caso de uso orquestador |

### 4.5 Presentación / configuración

| Origen | Destino |
|---|---|
| `report_formatter.py` (puro) | `infrastructure/adapters/report/` o caso de uso de presentación (formateo de salida) |
| `config.py` (raíz) y `presentation/config.py` | **no van a `src/`** (SKILL §1: no hay `config/`). Se inyectan vía `infrastructure/wirings/` o se pasan en el controller |
| `main.py` | driving adapter CLI en la **raíz** |
| `gradio_app.py` | driving adapter Web en la **raíz** |
| `process_feedback.py` | script auxiliar; fuera del núcleo (se evalúa al final) |

---

## 5. Catálogo de puertos (interfaces del dominio)

Todos con sufijo `Port` (no hay DB). Definidos en `domain/<entity>/`,
implementados en `infrastructure/adapters/<entity>/`.

| Puerto | Método(s) conceptual(es) | Adapter de producción | Doble de test |
|---|---|---|---|
| `LanguageModelPort` | `generate(prompt) -> str` | `OllamaAdapter` | `FakeLanguageModelAdapter` (respuesta fija) |
| `GrammarCheckPort` | `check(paragraphs) -> issues` | `LanguageToolAdapter` | `InMemoryGrammarAdapter` |
| `DocumentTextPort` | `read_paragraphs(path) -> list[str]` | `DocxTextAdapter` | `InMemoryDocumentAdapter` |
| `ContentExtractionPort` | `extract(paragraphs, path) -> DocumentContent` | `ParagraphContentAdapter` | doble en memoria |
| `CitationExtractionPort` | `extract_citations(path) -> list[Citation]` | `DocxCitationAdapter` | doble en memoria |
| `ReferenceExtractionPort` | `extract_references(path) -> (list[Reference], str)` | `DocxReferenceAdapter` | doble en memoria |
| `CharacterCountPort` | `count(path) -> Counts` | `Win32ComWordCountAdapter` | `FakeCharacterCountAdapter` |
| `ReportExportPort` | `export(result, path) -> bool` | `DocxReportAdapter` | doble en memoria |
| `DocumentFormatInspectionPort` | `inspect(doc, content) -> violations` | `DocxEumicAdapter` | doble en memoria |

**Regla de error (SKILL §5):** los métodos de los adapters se decoran con
`@generic_error_handler`. Los casos de uso y el dominio lanzan subclases
específicas de `BaseSrcError` (ver §7).

---

## 6. Catálogo de casos de uso (`src/application/`)

| Use case | Depende de (puertos) | Servicios de dominio | Salida |
|---|---|---|---|
| `ReadDocumentUseCase` | `DocumentTextPort` | — | `list[str]` párrafos |
| `ExtractContentUseCase` | `ContentExtractionPort`, `CharacterCountPort` | — | `DocumentContent` |
| `ClassifyArticleUseCase` | `LanguageModelPort` | `ArticleClassifier`, `classify_article_size` | `ClassificationResult` DTO |
| `AnalyzeQualityUseCase` | `LanguageModelPort` | `get_quality_level_from_score` | `QualityResult` DTO |
| `ValidateStructureUseCase` | — | `StructureValidator` | `StructureValidationResult` DTO |
| `ExtractCitationsUseCase` | `CitationExtractionPort`, `ReferenceExtractionPort` | — | citas + referencias |
| `MatchCitationsUseCase` | — | `CitationMatcher` | `CitationAnalysisResult` DTO |
| `ValidateApaUseCase` | — | `ApaValidator` | violaciones APA |
| `CheckGrammarUseCase` | `GrammarCheckPort` | — | score + feedback |
| `VerifyEumicUseCase` | `DocumentFormatInspectionPort` | — | violaciones EUMIC |
| `AnalyzeDocumentUseCase` (orquestador) | compone los anteriores | genera recomendaciones | `AnalysisResult` DTO |
| `ExportReportUseCase` | `ReportExportPort` | — | bool |

`AnalyzeDocumentUseCase` reemplaza a `SilvinaEditorialAssistant.analyze_document`
y a `_generate_recommendations`. La generación de recomendaciones es lógica de
dominio pura → servicio `RecommendationBuilder` en `domain/`.

---

## 7. Excepciones de dominio (`src/domain/exceptions/`)

Un archivo por grupo (SKILL §5). Cada excepción hereda de un tipo base de
`base_src_error.py` (ya existe).

| Archivo | Excepciones (ejemplos) | Hereda de |
|---|---|---|
| `document_errors.py` | `DocumentNotFound`, `DocumentEmpty`, `DocumentUnreadable` | `SrcBaseNotFound` / `SrcBaseWarning` |
| `citation_errors.py` | `CitationParsingFailed` | `SrcBaseWarning` |
| `classification_errors.py` | `ClassificationFailed` | `SrcBaseWarning` |
| `quality_errors.py` | `QualityAnalysisFailed` | `SrcBaseWarning` |
| `language_model_errors.py` | `LanguageModelUnavailable` | `SrcBaseWarning` |

Hoy el código usa `ValueError`, `Exception` genérica y `try/except` que imprimen.
Migrar a esta jerarquía es parte de cada slice. Los entry points (`main.py`,
`gradio_app.py`) capturan `BaseSrcError` y lo mapean a salida CLI/HTTP.

---

## 8. Estrategia incremental por slices verticales

Cada slice es **end-to-end** (dominio → puerto → adapter → wiring → test),
**mergeable solo** y deja el sistema funcionando. El código viejo sigue vivo
hasta que su slice equivalente esté migrado y verificado.

### Orden recomendado (de menor a mayor acoplamiento externo)

| # | Slice | Por qué en este orden | Puerto nuevo |
|---|---|---|---|
| **0** | **Fundaciones de dominio**: migrar enums, entidades base y DTOs sin I/O. Consolidar duplicados de `models.py`. | Todo lo demás depende de estos tipos. Sin dependencias externas. | — |
| **1** | **Excepciones de dominio**: poblar `<grupo>_errors.py`. | Los slices siguientes ya lanzan las excepciones correctas. | — |
| **2** | **ValidateStructure** (puro) | Sin infra. Valida el patrón servicio+use case+wiring+test con algo simple. | — |
| **3** | **ValidateApa** (puro) | Igual que el 2, refuerza el patrón. | — |
| **4** | **MatchCitations** (casi puro) | Aísla la única fuga de docx en un puerto. | (reusa extraction) |
| **5** | **ReadDocument** | Primer adapter de `python-docx`. Base para extracción. | `DocumentTextPort` |
| **6** | **ExtractContent** (+ conteo) | Depende de lectura; introduce `win32com`. | `ContentExtractionPort`, `CharacterCountPort` |
| **7** | **ExtractCitations / References** | Adapters de docx XML. | `CitationExtractionPort`, `ReferenceExtractionPort` |
| **8** | **ClassifyArticle** | Primer adapter de LLM (`Ollama`). | `LanguageModelPort` |
| **9** | **AnalyzeQuality** | Reusa `LanguageModelPort`. | (reusa) |
| **10** | **CheckGrammar** | Adapter `language_tool`. | `GrammarCheckPort` |
| **11** | **VerifyEumic** | Adapter docx de inspección de formato. | `DocumentFormatInspectionPort` |
| **12** | **ExportReport** | Adapter docx de escritura. | `ReportExportPort` |
| **13** | **AnalyzeDocument (orquestador)** + `RecommendationBuilder` | Compone todos los anteriores. | — |
| **14** | **CLI controller** (`main.py` → wiring) | El CLI arma el wiring del orquestador. | — |
| **15** | **Gradio controller** (`gradio_app.py` → wiring) | La UI web reutiliza el mismo use case. | — |
| **16** | **Limpieza final**: borrar `business_logic/`, `data_access/`, `domain/`, `presentation/` viejos; retirar tests pytest reemplazados. | Solo cuando todo lo anterior pasa. | — |

### Anatomía de un slice (Definition of Done)

Cada slice está **terminado** cuando:

1. ☐ Entidades/DTOs/enums que toca están en `src/domain/` con `unittest`.
2. ☐ Si cruza una frontera externa: puerto definido en `domain/<entity>/` +
   adapter en `infrastructure/adapters/<entity>/` con `@generic_error_handler`.
3. ☐ Caso de uso en `src/application/` que solo depende de `src/domain/`.
4. ☐ Wiring de producción en `infrastructure/wirings/<use_case>_wiring.py`.
5. ☐ Wiring de test en `infrastructure/tests/test_doubles/` con doble en memoria.
6. ☐ Tests `unittest.TestCase`: dominio puro + use case con doble + (opcional)
   integración del adapter real.
7. ☐ Imports cumplen invariantes del SKILL (§2 dirección, §3 estilo, sin imports
   locales, sin wildcard).
8. ☐ **Una clase por archivo**: sin funciones de módulo sueltas en el dominio
   (convertidas a clases/servicios o `@classmethod` factory — §4.2). Excepción:
   `domain/exceptions/`.
9. ☐ El sistema viejo sigue funcionando (coexistencia).

---

## 9. Convenciones y decisiones fijadas

| Tema | Decisión |
|---|---|
| Estrategia | Incremental por slices verticales, con coexistencia |
| Entry points | `main.py` y `gradio_app.py` **en la raíz**, fuera de `src/`, como driving adapters delgados |
| Alcance | Todo el sistema actual (5 features + lectura + export + 2 UIs) |
| Tests | Reescritos como `unittest.TestCase` dentro de `src/`; los pytest viejos se retiran al migrar su código |
| Estructura `src/` | **No se modifica.** Solo se rellena |
| Una clase por archivo | **POO total**: cada clase en su propio archivo (snake_case = PascalCase). Las funciones sueltas se convierten en clases de servicio o `@classmethod` factory (§4.2). Única excepción: `domain/exceptions/` agrupa excepciones (SKILL §4) |
| Puertos | Todos `Port` (no hay DB, ningún `Repository`) |
| Config | No va a `src/`; se inyecta vía wiring o controller |
| Python | 3.10+, `X | None` en vez de `Optional[X]`, imports de nombres específicos |
| Errores | Jerarquía `BaseSrcError`; adapters con `@generic_error_handler` |
| Orden de métodos en una clase | No aplica a dunder methods (`__init__` siempre primero). Después, métodos públicos y luego privados (prefijo `_`), **sin intercalar — regla dura, sin excepción**. Dentro de cada grupo, orden alfabético por nombre — preferente pero casi obligatorio: romperlo requiere una razón muy determinante y permiso explícito. Preferir nombres autoexplicativos sin números (ej. `_reasoning_full_signal_match`, no `_reasoning_case_2`) — si un número de todos modos debe quedar en el nombre, el orden numérico tiene prioridad sobre el alfabético estricto (`_2`/`_02` antes que `_19`/`_019`) |

---

## 10. Riesgos y puntos de atención

1. **`win32com` es solo Windows y requiere Word instalado.** El
   `CharacterCountPort` debe tener un adapter de fallback (o el `python-docx`
   adapter ya cubre el conteo aproximado). Hoy `word_counter` ya maneja
   `WIN32COM_AVAILABLE`. Mantener esa degradación elegante detrás del puerto.
2. **Ollama puede no estar disponible.** `LanguageModelPort` debe permitir un
   doble/fallback; hoy hay `try/except` que devuelven valores por defecto. Esa
   política pasa al caso de uso, no al adapter.
3. **Duplicación y bugs latentes en `models.py`/`enums.py`** (ver §4.1). No
   arrastrar los bugs: corregir al migrar cada tipo, documentando el cambio.
4. **`main.py` mezcla orquestación + presentación + I/O de archivos.** Hay que
   separar: orquestación → `AnalyzeDocumentUseCase`; presentación → controller.
   Cuidado con el formato exacto de `analysis_results` (dict) que consume
   `report_formatter`, `word_exporter` y `gradio_app`: definir el DTO de salida
   (`AnalysisResult`) como contrato estable antes del slice 13.
5. **Imports locales dispersos** (`from apa_validator import ...` dentro de
   métodos). Al migrar, todos suben al tope del archivo (SKILL §3).
6. **`citation_matcher` toca docx en un solo método** (`extract_all_citations`):
   ese método se mueve al adapter de extracción; el resto del matcher es dominio
   puro.
7. **Doble fuente de `config`** (raíz y `presentation/`). Unificar en el wiring.
8. **Paridad de comportamiento.** Como el sistema viejo coexiste, conviene una
   suite de caracterización (golden tests) sobre un `.docx` de ejemplo en
   `tests/fixtures/` para comparar salida vieja vs nueva en cada slice.

---

## 11. Próximos pasos sugeridos (para la etapa de implementación)

1. Validar este plan y ajustar el mapeo Entity/DTO del §4.1.
2. Arrancar por el **Slice 0** (fundaciones de dominio) usando el agente
   `clean-architecture` como guía normativa.
3. Establecer el golden test de caracterización (§10.8) antes de tocar lógica.
4. Avanzar slice por slice respetando la Definition of Done del §8.

---

*Fin del documento. No se implementó ningún cambio de código.*
