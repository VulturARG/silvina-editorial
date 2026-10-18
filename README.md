# Silvina Editorial Assistant v0.200

[![Version](https://img.shields.io/badge/version-v0.200-blue)](https://github.com/P-SAL/silvina-editorial)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-Active%20Development-yellow)](https://github.com/P-SAL/silvina-editorial)
[![Branch](https://img.shields.io/badge/dev%20branch-silvina__editorial__v200-orange)](https://github.com/P-SAL/silvina-editorial/tree/silvina_editorial_v200)

**AI-powered manuscript review for Spanish academic journals** | EUMIC compliance • APA 7 validation • Modular architecture • LLM-powered quality analysis • FastAPI web interface

---

## 📖 Overview

Silvina is an intelligent editorial assistant for **Revista Visión Conjunta** (Facultad Militar Conjunta - Universidad de la Defensa Nacional, Argentina). It automates academic manuscript review using **deterministic structural validation** and **selective AI-powered analysis**.

**Current Version:** v0.200 (Q4 2026)\
**Architecture:** Hexagonal Architecture (Domain → Application → Infrastructure)\
**LLM Integration:** Ollama (gemma4-26b-adapted, built from hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS)\
**Interface:** FastAPI + HTMX web UI + CLI\
**Output Location:** web interface: `Documents\Silvina\reports\` (Word report, JSON data); command line: `<document folder>\análisis` (Word, JSON and HTML reports)

---

## 🌿 Branch Structure & Development Workflow

```
main                    ← Production branch — stable, merged from dev
silvina_editorial_v200  ← Active development branch ← feature branches merge here
silvina_editorial_v100  ← Historical reference (read-only)
silvina_editorial_v09   ← Historical reference (read-only)
silvina_editorial_v08   ← Historical reference (read-only)
```

**Development workflow:**
1. Each change is developed on its own feature branch (`feat/…`, `fix/…`, `refactor/…`, `docs/…`) created from `silvina_editorial_v200`
2. The feature branch is merged into `silvina_editorial_v200` through a pull request
3. When a stable milestone is reached → merge to `main`
4. Never develop directly on `main` or on `silvina_editorial_v200`

Substantial features are planned in `odd/tasks/<feature-name>.md` before the first change and closed with one commit per task.

**Setup on development machine:**
```bash
git checkout silvina_editorial_v200
source .venv/Scripts/activate  # Windows Git Bash
```

**Development machines:**
- DESKTOP-OE2SEGH — AMD Ryzen 7 8700G, 32GB RAM
- DESKTOP-LN7Q8I6 — 8GB RAM (code editing only, no LLM inference)
- DESKTOP — AMD Ryzen 5 5600X, 32GB RAM, GPU: Radeon RX 7800 XT 16GB VRAM

---

## ✨ Key Features

### 🎨 **Web Interface**
- Drag-and-drop file upload
- Interactive result visualization
- One-click Word/JSON download
- Clean shutdown button

### ⌨️ **Command Line**
- `python main.py <document.docx>` runs the same analysis and writes the Word, JSON and HTML reports
- Starts and stops the Ollama server and preloads the model on its own
- Per-run overrides for the model, the mode and the prompts

### 🏗️ **Hexagonal Architecture**
```
src/domain/         # Entities, DTOs, enums, exceptions, and ports
src/application/    # Use cases (orchestrate domain behavior)
src/infrastructure/ # Adapters (docx, ollama, win32com, language_tool), wiring, and configuration
```

---

## 📚 Document Analysis Pipeline

**7-Step Process:**

1. **📖 Document Reading** — Extracts paragraphs from .docx
2. **🔍 Content Extraction** — Title, authors, sections, word count
3. **📚 Citation & Reference Parsing** — In-text citations, bibliography, APA 7 validation
4. **🏷️ Article Classification** — Hybrid signal system (S1–S5)
5. **⭐ Quality Analysis** — 4 semantic dimensions via LLM
6. **📋 Structure Validation** — Required sections per article type
7. **🔗 Citation Matching** — Links citations to references

---

## 🎯 Classification System — Hybrid Signal Approach (S1–S6)

### Signal Architecture

| Signal | Type | Criteria | Role |
|--------|------|----------|------|
| S1 — IMRyD sections | Deterministic | Title/section structure matches IMRyD | Direct path to CIENTÍFICO (0.95) |
| S2a — Reference count | Deterministic | ≥ 12 references | Confidence modulator |
| S2b — Reference recency | Deterministic | ≥ 50% within last 4 years | Confidence modulator |
| S3 — Methodological vocab | Deterministic | ≥ 4 terms + ≥ 1 hard term | Mandatory gate for CIENTÍFICO |
| S4 — Research intent | LLM (combined) | Explicit research intent detected | Primary gate for CIENTÍFICO |
| S5 — Conclusive contribution | LLM (combined) | Evidence-based contribution detected | Primary gate for CIENTÍFICO |
| S6 — Theoretical justification | LLM (combined) | Framework justification / knowledge gap identified | Confidence modulator |

**S4, S5 and S6 are evaluated in a single combined LLM call** for efficiency and consistency.

**S3 vocabulary covers:** quantitative methodology, qualitative/social science, experimental/simulation design, systematic review/meta-analysis, validation and results markers, metrics and measurement — in Spanish and English.

**S4 detects:** explicit goals or objectives, hypotheses posed, research questions, methodologies declared, and systematic processes outlined.

**S5 detects:** findings from systematic process, frameworks/models/taxonomies proposed, evidence-based recommendations, knowledge gaps addressed, synthesis beyond description, quantitative experimental results, hypothesis confirmation.

**S6 detects:** references to state of the art or prior literature, identification of knowledge gaps, theoretical framework justification, anchoring in prior research.

### Classification Rule — 19-Case Table

**CIENTÍFICO threshold: confidence ≥ 0.83.** Below this threshold, evidence is insufficient and the article classifies as DIVULGACIÓN.

| Case | Signals | Result | Confidence |
|------|---------|--------|------------|
| S1 | IMRyD override | CIENTÍFICO | 0.95 |
| 2 | S3+S4+S5+S2a+S2b+S6 | CIENTÍFICO | 0.90 |
| 3 | S3+S4+S5+S2b+S6 | CIENTÍFICO | 0.86 |
| 4 | S3+S4+S5+S2a+S2b | CIENTÍFICO | 0.85 |
| 5 | S3+S4+S5+S2a+S6 | CIENTÍFICO | 0.83 |
| 6 | S3+S4+S5+S6 | DIVULGACIÓN ⚠ | — |
| 7 | S3+S4+S5+S2b | DIVULGACIÓN ⚠ | — |
| 8 | S3+S4+S5+S2a | DIVULGACIÓN ⚠ | — |
| 9 | S3+S4+S5 | DIVULGACIÓN ⚠ | — |
| 10 | S3+S4 | DIVULGACIÓN | — |
| 11 | S3+S5 | DIVULGACIÓN | — |
| 12 | S3+S2a+S2b | DIVULGACIÓN | — |
| 13 | S3+S2a | DIVULGACIÓN | — |
| 14 | S3+S2b | DIVULGACIÓN | — |
| 15 | S3 alone | DIVULGACIÓN | — |
| 16 | S4+S5 (no S3) | DIVULGACIÓN | — |
| 17 | S4 alone | DIVULGACIÓN | — |
| 18 | S5 alone | DIVULGACIÓN | — |
| 19 | No signals | OPINIÓN | — |

⚠ Cases 6–9: S3+S4+S5 qualitative core present but below threshold. Silvina emits a specific editorial recommendation identifying which signals are missing and what author corrections could bring the article to threshold.

**Confidence levels apply exclusively to CIENTÍFICO.** DIVULGACIÓN and OPINIÓN carry no confidence value — they represent a determination that evidence for CIENTÍFICO is insufficient, not a degree of certainty about an alternative category.

### Design Principles
- **S1 owns the absolute ceiling at 0.95** — deterministic IMRyD override
- **S2–S6 system ceiling is 0.90** — no LLM-dependent combination can equal S1 certainty
- **S3 is the mandatory methodological gate** — without S3, CIENTÍFICO is impossible
- **S4+S5 are the primary qualitative discriminators** — both required together with S3
- **S6 modulates confidence** — raises CIENTÍFICO confidence but never gates classification
- **S2a/S2b modulate confidence** — bibliographic support but do not determine category
- **S4/S5/S6 non-determinism on CPU is a known hardware limitation** — GPU inference (v1.0) will resolve this

### Structure Validation by Classification Path
- **S1 classified (IMRyD):** requires full IMRyD sections (Metodología, Resultados, Discusión)
- **S2–S6 classified:** requires DIVULGACIÓN sections (Resumen, Introducción, Desarrollo, Conclusiones, Referencias)

---

## ⭐ Quality Analysis

**4 Semantic Dimensions:**
- **Claridad** — Writing clarity and readability
- **Coherencia** — Logical flow and consistency
- **Argumentación** — Strength of arguments and evidence
- **Conclusiones** — Quality and relevance of conclusions

**Architecture:** Single combined LLM call per dimension pair (Call 1: Claridad + Coherencia / Call 2: Argumentación + Conclusiones). Score inference from narrative when LLM omits score format.

**Full body analysis:** the classification, quality and editorial suitability prompts receive the whole article body (title and body paragraphs), with no sampling or truncation. The grammar check also covers the abstract and the whole body.

**Article body:** Silvina locates the body between the article header and the bibliography header (`[bibliography]` in `editorial_norms.toml`). The body size sets the article size band (`[article_size]` in `analysis_settings.toml`, which now includes an extra long band), and an article whose body exceeds `max_body_chars` (`[article_length]`, 75 000 characters by default) is rejected before the analysis.

**Tables:** the tables of the document are read with their position and sent to the classification, quality and editorial suitability prompts as Markdown tables, placed between the paragraphs that surround them in the original. They do not count toward the body length and do not change citations, references, grammar, sections or word counts. Images are not sent; the prompts carry only their captions.

---

## 📊 Multi-Format Reports

**Web interface** — 2 files saved to `C:\Users\[user]\Documents\Silvina\reports\` (or the directory in `SILVINA_REPORTS_DIR`):
1. **📘 Word Report** (`_analisis.docx`)
2. **📊 JSON Data** (`_analisis.json`), including the editorial suitability

**Command line** — 3 files in `<document folder>\análisis` (or `--output-dir`): the Word report, the JSON data and an **HTML report** (`.html`).

The Word report lists every APA 7 violation, states the display limit when grammar errors are truncated, and marks the unmet EUMIC norms section as informative.

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Web Interface | FastAPI + HTMX |
| Document Parsing | python-docx |
| Word Automation | win32com (Windows COM) |
| LLM Integration | Ollama (local inference) |
| Grammar Checking | LanguageTool |
| Architecture | Hexagonal Architecture |

---

## 📦 Installation

```bash
# 1. Clone repository
git clone https://github.com/P-SAL/silvina-editorial.git
cd silvina-editorial

# 2. Switch to development branch
git checkout silvina_editorial_v200

# 3. Create the virtual environment and install dependencies (Windows)
setup.bat
source .venv/Scripts/activate  # Windows Git Bash

# 4. Or do it manually
python -m venv .venv
pip install -r requirements.txt

# 5. Install the LLM model (requires Ollama 0.35.0 or newer)
scripts\create_ollama_model.bat
```

The application uses `gemma4-26b-adapted`, a local Ollama model built from the Unsloth GGUF `hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS` with the versioned Modelfile in `src/infrastructure/resources/ollama/`. The raw GGUF declares no thinking capability, so `OLLAMA_THINK=false` cannot work on it and thinking tags leak into the answers; the adapted model adds the `gemma4` renderer and parser. The script pulls the base only when it is missing and then runs `ollama create`. The manual equivalent is:

```bash
ollama pull hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS
ollama create gemma4-26b-adapted -f src/infrastructure/resources/ollama/gemma4-26b-adapted.Modelfile
```

The base GGUF tag is published by a third party and can change upstream, so a model rebuilt later may use different weights bytes than an earlier build.

### Configuration files

Silvina reads its configuration from three places:

- `analysis_settings.toml` (project root, versioned): the tuning parameters, grouped by section (`[grammar]`, `[article_size]`, `[recommendation]`, `[report]`, `[upload]`, and others). Edit it to adjust thresholds and size bands.
- `editorial_norms.toml` (project root, versioned): the editorial norms that Silvina checks documents against: the document format (`[document_format]`: margins, font size, allowed fonts and the unjustified paragraph ratio), the caption prefixes for figures and tables (`[figures]`, `[tables]`), the abstract and keyword limits (`[abstract]`, `[keywords]`), and the sections required by each article type with their aliases (`[required_sections]`, `[section_aliases]`).
- `.env` (not versioned, see `.env.example`): the values that depend on the machine or the deployment, such as `APP_MODE`, `METRICS_DATABASE_PATH`, `LOG_FILE_PATH` and the Ollama connection.

An environment variable with the same name as a setting (for example `GRAMMAR_MAX_REPLACEMENTS`) overrides the value in `analysis_settings.toml`, so a line left in your local `.env` wins over the file on that machine. If a setting is missing from both, or has the wrong type, the application stops at startup with a message naming the section and key. The parameters that live in `.env` have no default in the code: if one is missing or blank, the application stops at startup naming the variable (`OLLAMA_NUM_CTX` is the only optional one: without it Ollama decides the context size).

No environment variable overrides `editorial_norms.toml`; its values are read only from the file. Silvina reads it once, when it starts. If the file is missing or is not valid TOML, or if a key is missing or has an invalid value, the application stops at startup with a message that names the file, or the section and key.

To change a norm, edit its value in `editorial_norms.toml`, keep the type of the value (numbers without quotes, text in double quotes, lists in square brackets), and restart the application. The labels must match the existing names:

- The keys of `[required_sections]` are article types: `"científico"`, `"divulgación"` and `"opinión"`. All three must be present.
- Each list in `[required_sections]` names sections from the list below, and each of those sections must have an entry in `[section_aliases]`.
- The keys of `[section_aliases]` are section names: `"Resumen"`, `"Introducción"`, `"Metodología"`, `"Resultados"`, `"Discusión"`, `"Argumentación"`, `"Desarrollo"`, `"Conclusiones"` and `"Referencias"`.
- An alias is the word that identifies a section header. Aliases are compared in lowercase, and the order of the entries in `[section_aliases]` matters: the first section whose alias matches a header wins.

### Ollama warm-up and keep_alive

When the web server starts (`launch_silvina.bat` or `python web_main.py`) and Ollama is the language model in use, Silvina loads the model in the background so the first analysis does not pay the load time (about a minute for the 26B model). The server answers while the model loads, and a failed warm-up only writes a warning to the log. Every request also asks Ollama to keep the model loaded for a while after its last use, instead of the 5 minutes of the Ollama default.

| Variable | Value in `.env.example` | Meaning |
|----------|---------|---------|
| `OLLAMA_WARMUP_ON_STARTUP` | `true` | `true` or `false`. Loads the model when the server starts |
| `OLLAMA_MODEL_KEEP_ALIVE` | `15m` | How long the model stays loaded after each request. A duration with a unit (`15m`, `1h`, `90s`); a negative one such as `-1m` keeps it loaded indefinitely |
| `OLLAMA_SERVER_IDLE_SHUTDOWN` | `5m` | Inactivity duration before closing a server started by the CLI. A strictly positive duration with a unit (`5m`, `90s`, `1h`) |

The warm-up is skipped when the external LLM (Claude, `APP_MODE=DEBUG` only) is in use; when a local Ollama model is used, the warm-up runs in the web interface on startup and also in the command line as its own announced step. While loaded, the 26B model holds about 14 GB of VRAM: if the same GPU is shared with other applications, lower `OLLAMA_MODEL_KEEP_ALIVE` or set `OLLAMA_WARMUP_ON_STARTUP=false`. `OLLAMA_MODEL_KEEP_ALIVE` is Silvina's setting and is independent from the `OLLAMA_KEEP_ALIVE` variable of the Ollama server.

### Optional: external LLM for debugging (Claude)

In `APP_MODE=DEBUG` the analysis can use Claude through the Claude Agent SDK instead of Ollama, with a Claude subscription (no API key):

```bash
pip install -r requirements-debug.txt
claude login
```

Then set in `.env`:

```dotenv
APP_MODE=DEBUG
USE_EXTERNAL_LLM=true
LLM_PROVIDER=claude
EXTERNAL_LLM_MODEL_NAME=<claude model name>
```

`USE_EXTERNAL_LLM` (`true` or `false`, required) enables the external LLM instead of Ollama. `LLM_PROVIDER` names only the external provider (`claude`) and `EXTERNAL_LLM_MODEL_NAME` is its model, independent from `OLLAMA_MODEL_NAME`; both are required when the flag is `true`. `EXTERNAL_LLM_THINK` (`true` or `false`, required) controls the model's reasoning: with `false` the Claude adapter disables it, which cut a classification call from about 16 s and 1600 output tokens to about 4 s and 17 tokens. With the flag `false`, or with `APP_MODE=PROD`, Ollama is used and `LLM_PROVIDER` and `EXTERNAL_LLM_MODEL_NAME` are ignored. The Ollama generation options (`temperature`, `num_predict`) are not applied to external providers.

---

## 🚀 Usage

### Web Interface
```bash
launch_silvina.bat
```

Or, with the virtual environment active:

```bash
python web_main.py
```

### Command Line
```bash
python main.py <document.docx>
```

The document is read from the current directory unless `--input-dir` is given. Only `.docx` files are accepted. If the document name is omitted, the console asks for it. The console shows the start and the end of each step, and the paths of the generated reports at the end.

| Option | Description |
|--------|-------------|
| `--input-dir <dir>` | Directory where the document is read (default: current directory) |
| `--output-dir <dir>` | Directory for the reports (default: `<document folder>/análisis`, created when missing) |
| `--ollama-model-name <name>` | Overrides `OLLAMA_MODEL_NAME` |
| `--use-external-llm true\|false` | Overrides `USE_EXTERNAL_LLM` |
| `--llm-provider <name>` | Overrides `LLM_PROVIDER` |
| `--external-llm-model-name <name>` | Overrides `EXTERNAL_LLM_MODEL_NAME` |
| `--app-mode DEBUG\|PROD` | Overrides `APP_MODE` |
| `--prompts-dir <dir>` | Root of a complete prompt set that replaces the default `src/infrastructure/resources/prompts`: a directory with the `classification/` and `quality/` folders and the same file names as the default one |
| `--s4-s5-s6-signal-prompt <dir>` | Directory containing `s4_s5_s6_signal_prompt.txt` to override default signal prompt |
| `--alignment-prompt <dir>` | Directory containing `alignment_prompt.txt` to override default alignment prompt |
| `--argumentation-conclusions-prompt <dir>` | Directory containing `argumentation_conclusions_prompt.txt` to override default argumentation prompt |
| `--clarity-coherence-prompt <dir>` | Directory containing `clarity_coherence_prompt.txt` to override default clarity and coherence prompt |
| `--contribution-prompt <dir>` | Directory containing `contribution_prompt.txt` to override default contribution prompt |
| `--research-lines <dir>` | Directory containing `research_lines.txt` to override default research lines |

The external LLM is only used when the mode is `DEBUG`, as with the `.env` settings.

When a local Ollama model is used, the CLI verifies that the language model server is reachable in its own announced step (`Verificando el servidor del modelo de lenguaje`). If the local Ollama server is not running, the CLI starts the system `ollama serve` process and waits up to the timeout limit. The executable is looked up in the PATH, then in the system-wide persistent PATH, then in `%LOCALAPPDATA%\Programs\Ollama`, so a terminal opened before installing Ollama still works. A server started by the CLI is closed after 5 minutes without use by a background watcher process (configurable through `OLLAMA_SERVER_IDLE_SHUTDOWN`), while a server that was already running is never touched; a second CLI run within the window restarts the count. Next, when warm-up is enabled (`OLLAMA_WARMUP_ON_STARTUP=true`), the model is preloaded before the analysis in its own announced step (`Precargando el modelo de lenguaje`). When using an external model, both server check and warm-up steps are skipped.

Each run writes three reports, `<document>_analisis_<model>.docx`, `.json` and `.html`, overwriting any previous files with the same names. When the run uses a non-default prompt source, the three names gain the same suffix: an underscore followed by the `--prompts-dir` folder name and the replaced prompt names, joined with `+` (the word `default` never appears). With model `claude-haiku-5-5`:

- `doc_analisis_claude-haiku-5-5_v2.docx`: `--prompts-dir` pointing to a folder named `v2`, no per-prompt flags.
- `doc_analisis_claude-haiku-5-5_v2+alignment_prompt.docx`: the same folder, with `alignment_prompt` replaced.
- `doc_analisis_claude-haiku-5-5_clarity_coherence_prompt+research_lines.docx`: default prompts, with `clarity_coherence_prompt` and `research_lines` replaced.

Runs with different prompt sources therefore no longer overwrite each other. Runs with the same prompt source and model still overwrite each other.

```bash
python main.py documento.docx --input-dir C:\Trabajos --output-dir C:\Informes --app-mode PROD
```

Prompt files can be overridden individually by pointing to a directory that contains the matching `.txt` file:

```bash
python main.py documento.docx --alignment-prompt C:\mis_prompts
```

A whole prompt set can be replaced at once with `--prompts-dir`. The directory must contain `classification/s4_s5_s6_signal_prompt.txt` and `quality/{alignment_prompt,argumentation_conclusions_prompt,clarity_coherence_prompt,contribution_prompt,research_lines}.txt`; a missing file is a usage error and the packaged prompts are never used as a silent fallback. The per-prompt flags above still take precedence over the directory.

```bash
python main.py documento.docx --prompts-dir src\infrastructure\resources\prompts\v2
```

Each CLI run records which prompts it used, in the log (`Prompt source: ...`) and in the Word, JSON and HTML reports (`Prompts utilizados`, the `prompt_source` key and a line at the top of the HTML page). The value is `default` or the name of the `--prompts-dir` folder, followed by the replaced prompts when per-prompt flags are used, for example `v2 + alignment_prompt`. The web reports do not show it.

---

## 📁 Project Structure
```
silvina-editorial/
├── main.py                      # Command line entry point
├── web_main.py                  # Web server entry point
├── launch_silvina.bat
├── setup.bat
├── version.txt
├── requirements.txt
├── analysis_settings.toml
├── editorial_norms.toml
├── scripts/                     # Ollama model creation and fixture tools
├── sandbox/                     # Sample documents for manual testing
├── odd/tasks/                   # Feature plans, one document per feature
├── docs/                        # Design and study documents
├── src/
│   ├── domain/                  # Entities, DTOs, enums, exceptions, and ports
│   │   ├── citation/
│   │   ├── classification/
│   │   ├── document/
│   │   ├── dtos/
│   │   ├── entities/
│   │   ├── enums/
│   │   ├── exceptions/
│   │   ├── gateway/
│   │   ├── grammar/
│   │   ├── language_model/
│   │   ├── metrics/
│   │   ├── ports/
│   │   ├── quality/
│   │   ├── recommendation/
│   │   ├── report/
│   │   └── structure/
│   ├── application/             # Use cases (orchestrate domain behavior)
│   │   ├── analyze_document_use_case.py
│   │   ├── export_report_use_case.py
│   │   ├── ensure_language_model_server_use_case.py
│   │   ├── release_language_model_server_use_case.py
│   │   └── warm_up_language_model_use_case.py
│   └── infrastructure/          # Adapters, config, and wirings
│       ├── adapters/
│       │   ├── document/
│       │   ├── gateway/
│       │   ├── grammar/
│       │   ├── llm_generator/
│       │   ├── metrics/
│       │   └── report/
│       ├── cli/
│       ├── fastapi/
│       ├── resources/           # Prompts and the Ollama Modelfile
│       ├── env_config.py
│       └── wirings/
└── tests/                       # Integration and unit tests (unit tests also live next to each layer)
    ├── e2e/
    ├── fixtures/
    ├── smoke/
    └── test_main_cli_args.py
```

---

## 🔄 Version History

### v0.200 (Q4 2026) — Current

- 📄 **Whole article body analysis:** the classification, quality, editorial suitability and grammar checks read the whole article body instead of a text sample. The body is located between the header and the bibliography, driven by `editorial_norms.toml`.
- 📏 **Article length:** new extra long size band, and articles above `max_body_chars` are rejected before the analysis.
- 📊 **Tables in the prompts:** document tables reach the classification, quality and editorial suitability prompts as Markdown, at their original position.
- 🧾 **JSON report** now includes the editorial suitability.
- 🔧 **FIXED (document):** the title and the authors are taken from the article header.
- 🔧 **FIXED (citations):** every citation of a parenthetical group separated by semicolons is extracted; each reference is read from its own paragraph; parentheses with dates and document codes are not citations; the ampersand of corporate authors is kept; a citation matches the acronym declared in its reference.
- 🔧 **FIXED (quality):** dimensions are matched from the section header line, the response is split only at bold lines that carry a score, only the recommendation paragraph is dropped from a feedback, and a heading that groups several titled sections is kept. Quality levels use the thresholds from `analysis_settings.toml` (`[quality_level]`).
- 🔧 **FIXED (report):** every APA 7 violation is listed, the grammar truncation limit is stated, the unmet EUMIC norms section is marked as informative, out-of-norm font sizes are worded in singular and plural, and the closing separator fits the page width.

### v0.100 (Q3 2026)

- 🌐 **FastAPI + HTMX web interface** replaces Gradio (`web_main.py`, started by `launch_silvina.bat`).
- 📄 **JSON report export** next to the Word report.
- 📊 **Internal metrics and AI audit** in SQLite: per-analysis and per-stage durations, and every language model call with its token usage and `done_reason`.
- 🤖 **Ollama**: reasoning disabled by default through `OLLAMA_THINK`; the official model is `gemma4-26b-adapted`, built from a versioned Modelfile with `scripts/create_ollama_model.bat`.
- 🧪 **External LLM for debugging (Claude)** in `APP_MODE=DEBUG`.
- 🔧 **FIXED:** classification signals S2a/S2b could never be satisfied because references were not extracted; reports keep the uploaded file name and a unique folder per analysis; specific language model error messages; concurrent analyses are cancelled or serialized; feedback rendering in the Word report.
- ♻️ **Refactor:** the feedback, quality and editorial suitability parsers were rebuilt on single-purpose collaborators.
- **Editorial norms file:** the EUMIC format, abstract and keyword limits, required sections per article type and section aliases are read from `editorial_norms.toml` instead of the code. A missing or invalid norm stops the application at startup.
- **Tuning file renamed:** the tuning parameters live in `analysis_settings.toml`. The Word report takes the publication threshold from it (`PUBLISH_THRESHOLD`), the same value used for the recommendations.

### v0.95 (Q2 2026)

- 🏗️ **Hexagonal Architecture migration**: Clean hexagonal codebase reorganization moving from the legacy 4-layer structure to Domain, Application, and Infrastructure layers.

### v0.9 (Q2 2026)

**Classification System — S6 Revision (May 2026):**
- ✨ **NEW:** S6 (Justificación teórica) — sixth signal detecting theoretical framework justification and knowledge gap identification, added to the combined S4/S5 LLM call (now S4/S5/S6, single call, zero extra latency)
- ✨ **NEW:** CIENTÍFICO threshold raised to confidence ≥ 0.83 — below threshold classifies as DIVULGACIÓN
- ✨ **NEW:** 19-case classification table replacing previous partial-signal CIENTÍFICO cases
- ✨ **NEW:** Cases 6–9 (S3+S4+S5 near-miss) → DIVULGACIÓN with specific editorial recommendation per case
- ✨ **NEW:** S1 ceiling 0.95 / S2–S6 system ceiling 0.90 — structural separation of deterministic vs LLM-dependent confidence
- ✨ **NEW:** DIVULGACIÓN and OPINIÓN carry confidence=None — they are insufficient-evidence determinations, not alternative category scores
- ✨ **NEW:** LLM response parser upgraded to regex — handles verbose model responses in any format
- ✨ **NEW:** num_predict raised from 30 to 300 — ensures model completes all three signal answers
- 🔧 **FIXED:** None confidence crashes in main.py, word_exporter.py — all confidence format strings guarded
- ✨ **NEW:** security.py module — FileValidator, PathGuard, RateLimiter, PromptInjectionDetector, auto_cleanup()

**Classification System — Earlier May 2026 revision:**
- ✨ **NEW:** S3 expanded vocabulary — quantitative, qualitative/social science, experimental/simulation, systematic review, validation/results, metrics in Spanish and English
- ✨ **NEW:** S4+S5 combined into single LLM call
- ✨ **NEW:** Structure validator path-aware — S2–S5 classified CIENTÍFICO uses DIVULGACIÓN structure requirements
- 🔧 **FIXED:** APA validator false positives — institutional acronyms (PLANCAMIL, UNESCO), identifiers (arXiv:), date ranges
- 🔧 **FIXED:** Author extraction — multi-line author lists (semicolon-separated) across up to 3 continuation paragraphs
- 🔧 **FIXED:** Title extraction — lines with semicolons correctly identified as author lists

**Earlier v0.9:**
- ✨ **NEW:** 5-signal hybrid classification engine
- ✨ **NEW:** Bibliography-aware text sampling (3500+2500 chars)
- ✨ **NEW:** `references` field added to `DocumentContent`
- 🔧 **FIXED:** IMRyD false positives in structure analyzer
- 🔧 **FIXED:** Citation matcher `_normalize_author()` — 13.8% → 93.1% match rate
- 🔧 **FIXED:** Quality analyzer call 2 parser — handles numbered and unnumbered headers
- 🔧 **FIXED:** Reference parser — `Fuentes bibliográficas consultadas` support
- 🔧 **FIXED:** Publishability verdict logic

### v0.8 (Q1 2026)
- Gradio web interface, feedback pipeline, two-call LLM quality analysis

### v0.7 (January 2026)
- EUMIC compliance, grammar checker, APA 7 validation

### v0.6 (December 2025)
- Citation-reference validation, IMRyD detection

---

## 🗺️ Roadmap

### v0.200 (Q4 2026) — Active Development
- ✅ Whole article body analysis, article size bands and length limit
- ✅ Document tables in the prompts
- ✅ Classification system S6 revision — 19-case table, 0.83 threshold
- ✅ S3 vocabulary expansion
- ✅ Confidence calibration (0.83/0.85/0.86/0.90/0.95)
- ✅ Structure validator path-aware fix
- ✅ APA validator false positive fix
- ✅ Author extraction multi-line fix
- ✅ Citation matcher improvements
- ✅ Branch-based workflow established
- ⬜ Security measures (file validation, authentication, rate limiting)
- ⬜ Web deployment preparation

### v0.100 → v1.0 (Security & Deployment)
- 🔒 File validation, defusedxml, path traversal protection
- 🔒 Authentication and rate limiting
- 🔒 Prompt injection detection
- 🌐 nginx + HTTPS deployment
- 🌐 Supervised availability model (institutional server)

### v1.0
- 🏢 Production deployment at Universidad de la Defensa
- 🖥️ Hardware upgrade: 64GB RAM + GPU (RTX 4060/4070)
- 🤖 Model upgrade: llama3.1:70b q4_K_M — deterministic S4/S5/S6 inference
- 📊 Editorial analytics dashboard

### v2.0 (Future)
- 🧠 Editorial memory (RAG-based)
- 🤖 Multi-agent R+D orchestration
- 🔄 Batch processing

---

## 🐛 Known Issues & Limitations

| Issue | Status | Notes |
|-------|--------|-------|
| S4/S5/S6 non-determinism on CPU | Known hardware limitation | GPU inference (v1.0) resolves this |
| Misspelling not detected | Deferred | LanguageTool filter excludes misspellings to avoid false positives on proper nouns |
| Pleonasm/wordiness not detected | Deferred | No free Spanish deterministic engine available |
| Citation matching on institutional refs | Partial | NIST, MITRE, arXiv-style citations have low match rates by design |
| Windows-only COM automation | By design | Falls back to python-docx on other platforms |
| Quality analyzer "No disponible" | Intermittent | LLM response format variance on very long documents |

---

## 🤝 Contributing

**Contact:** Pablo Salonio — plsalonio@gmail.com

**Contributors:**
- Pablo Salonio (GitHub: P-SAL)
- Luis Briones (GitHub: VulturARG)

**Repository:** https://github.com/P-SAL/silvina-editorial\
**Active branch:** `silvina_editorial_v200`

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- **Revista Visión Conjunta** — Editorial team for requirements and testing
- **Facultad Militar Conjunta** — Universidad de la Defensa Nacional
- **Ollama Team** — Local LLM infrastructure

---

**Last Updated:** October 2026\
**Version:** 0.200\
**Active Branch:** silvina_editorial_v200\
**Status:** Active Development 🚀
