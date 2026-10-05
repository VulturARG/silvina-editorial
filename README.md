# Silvina Editorial Assistant v0.100

[![Version](https://img.shields.io/badge/version-v0.100-blue)](https://github.com/P-SAL/silvina-editorial)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-Active%20Development-yellow)](https://github.com/P-SAL/silvina-editorial)
[![Branch](https://img.shields.io/badge/dev%20branch-silvina__editorial__v100-orange)](https://github.com/P-SAL/silvina-editorial/tree/silvina_editorial_v100)

**AI-powered manuscript review for Spanish academic journals** | EUMIC compliance • APA 7 validation • Modular architecture • LLM-powered quality analysis • FastAPI web interface

---

## 📖 Overview

Silvina is an intelligent editorial assistant for **Revista Visión Conjunta** (Facultad Militar Conjunta - Universidad de la Defensa Nacional, Argentina). It automates academic manuscript review using **deterministic structural validation** and **selective AI-powered analysis**.

**Current Version:** v0.100 (Q4 2026)
**Architecture:** Hexagonal Architecture (Domain → Application → Infrastructure)
**LLM Integration:** Ollama (gemma4-26b-adapted, built from hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS)
**Interface:** FastAPI + HTMX web UI + CLI
**Output Location:** `Documents\Silvina\reports\` (Word report, JSON data)

---

## 🌿 Branch Structure & Development Workflow

```
main                    ← Production branch — stable, merged from dev
silvina_editorial_v100  ← Active development branch ← ALL work goes here
silvina_editorial_v09   ← Historical reference (read-only)
silvina_editorial_v08   ← Historical reference (read-only)
```

**Development workflow:**
1. All code changes happen on `silvina_editorial_v09`
2. Push to `silvina_editorial_v09` after each session
3. When a stable milestone is reached → merge to `main`
4. Never develop directly on `main`

**Setup on development machine:**
```bash
git checkout silvina_editorial_v100
cd silvina_editorial
source ../venv312/Scripts/activate  # Windows Git Bash
```

**Primary development machine:** DESKTOP-OE2SEGH (32GB RAM, Ryzen 7 8700G)
**Secondary machine:** DESKTOP-LN7Q8I6 (8GB RAM) — code editing only, no LLM inference

---

## ✨ Key Features

### 🎨 **Web Interface**
- Drag-and-drop file upload
- Interactive result visualization
- One-click Word/JSON download
- Clean shutdown button

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

**Text sampling:** First 3500 chars (intro) + last 2500 chars (conclusions), bibliography excluded via paragraph-level header detection.

---

## 📊 Multi-Format Reports

**2 Output Files** saved to `C:\Users\[user]\Documents\Silvina\reports\`:
1. **📘 Word Report** (`_analisis.docx`)
2. **📊 JSON Data** (`_analisis.json`)

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
git checkout silvina_editorial_v100
cd silvina_editorial_v100

# 3. Create virtual environment
python -m venv ../venv312
source ../venv312/Scripts/activate  # Windows Git Bash

# 4. Install dependencies
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

### Ollama warm-up and keep_alive

When the web server starts (`launch_silvina.bat` or `python web_main.py`) and Ollama is the language model in use, Silvina loads the model in the background so the first analysis does not pay the load time (about a minute for the 26B model). The server answers while the model loads, and a failed warm-up only writes a warning to the log. Every request also asks Ollama to keep the model loaded for a while after its last use, instead of the 5 minutes of the Ollama default.

| Variable | Default | Meaning |
|----------|---------|---------|
| `OLLAMA_WARMUP_ON_STARTUP` | `true` | `true` or `false`. Loads the model when the server starts |
| `OLLAMA_MODEL_KEEP_ALIVE` | `15m` | How long the model stays loaded after each request. A duration with a unit (`15m`, `1h`, `90s`); a negative one such as `-1m` keeps it loaded indefinitely |

The warm-up is skipped when the external LLM (Claude, `APP_MODE=DEBUG` only) is in use, and it applies only to the web interface, not to the command line. While loaded, the 26B model holds about 14 GB of VRAM: if the same GPU is shared with other applications, lower `OLLAMA_MODEL_KEEP_ALIVE` or set `OLLAMA_WARMUP_ON_STARTUP=false`. `OLLAMA_MODEL_KEEP_ALIVE` is Silvina's setting and is independent from the `OLLAMA_KEEP_ALIVE` variable of the Ollama server.

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

`USE_EXTERNAL_LLM` (`true` or `false`, default `false`) enables the external LLM instead of Ollama. `LLM_PROVIDER` names only the external provider (`claude`) and `EXTERNAL_LLM_MODEL_NAME` is its model, independent from `OLLAMA_MODEL_NAME`; both are required when the flag is `true`. `EXTERNAL_LLM_THINK` (`true` or `false`, default `false`) controls the model's reasoning: with `false` the Claude adapter disables it, which cut a classification call from about 16 s and 1600 output tokens to about 4 s and 17 tokens. With the flag `false`, or with `APP_MODE=PROD`, Ollama is used and `LLM_PROVIDER` and `EXTERNAL_LLM_MODEL_NAME` are ignored. The Ollama generation options (`temperature`, `num_predict`) are not applied to external providers.

---

## 🚀 Usage

### Web Interface
```bash
python web_main.py
```

### Command Line
```bash
python main.py
```

---

## 📁 Project Structure
```
silvina_editorial_v100/
├── main.py
├── web_main.py
├── version.txt
├── requirements.txt
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
│   │   ├── ports/
│   │   ├── quality/
│   │   ├── recommendation/
│   │   ├── report/
│   │   └── structure/
│   ├── application/             # Use cases (orchestrate domain behavior)
│   │   ├── analyze_document_use_case.py
│   │   └── export_report_use_case.py
│   └── infrastructure/          # Adapters, config, and wirings
│       ├── adapters/
│       │   ├── document/
│       │   ├── gateway/
│       │   ├── grammar/
│       │   ├── llm_generator/
│       │   └── report/
│       ├── config/
│       ├── env_config.py
│       └── wirings/
└── tests/                       # Integration and unit tests
    ├── e2e/
    ├── fixtures/
    ├── smoke/
    └── test_main_cli_args.py
```

---

## 🔄 Version History

### v0.100 (Q4 2026) — Current

- 🌐 **FastAPI + HTMX web interface** replaces Gradio (`web_main.py`, started by `launch_silvina.bat`).
- 📄 **JSON report export** next to the Word report.
- 📊 **Internal metrics and AI audit** in SQLite: per-analysis and per-stage durations, and every language model call with its token usage and `done_reason`.
- 🤖 **Ollama**: reasoning disabled by default through `OLLAMA_THINK`; the official model is `gemma4-26b-adapted`, built from a versioned Modelfile with `scripts/create_ollama_model.bat`.
- 🧪 **External LLM for debugging (Claude)** in `APP_MODE=DEBUG`.
- 🔧 **FIXED:** classification signals S2a/S2b could never be satisfied because references were not extracted; reports keep the uploaded file name and a unique folder per analysis; specific language model error messages; concurrent analyses are cancelled or serialized; feedback rendering in the Word report.
- ♻️ **Refactor:** the feedback, quality and editorial suitability parsers were rebuilt on single-purpose collaborators.

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

### v0.100 (Q4 2026) — Active Development
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

### v1.0 (Q3 2026)
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

**Contact:** Pablo Salonio (P-SAL) — plsalonio@gmail.com
**Repository:** https://github.com/P-SAL/silvina-editorial
**Active branch:** `silvina_editorial_v100`

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- **Revista Visión Conjunta** — Editorial team for requirements and testing
- **Facultad Militar Conjunta** — Universidad de la Defensa Nacional
- **Ollama Team** — Local LLM infrastructure
- **Claude (Anthropic)** — Development assistance

---

**Last Updated:** October 2026
**Version:** 0.100
**Active Branch:** silvina_editorial_v100
**Status:** Active Development 🚀
