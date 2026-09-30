# Silvina Editorial Assistant v0.95

[![Version](https://img.shields.io/badge/version-v0.95-blue)](https://github.com/P-SAL/silvina-editorial)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-Active%20Development-yellow)](https://github.com/P-SAL/silvina-editorial)
[![Branch](https://img.shields.io/badge/dev%20branch-silvina__editorial__v095-orange)](https://github.com/P-SAL/silvina-editorial/tree/silvina_editorial_v095)

**AI-powered manuscript review for Spanish academic journals** | EUMIC compliance • APA 7 validation • Modular architecture • LLM-powered quality analysis • Gradio web interface

---

## 📖 Overview

Silvina is an intelligent editorial assistant for **Revista Visión Conjunta** (Facultad Militar Conjunta - Universidad de la Defensa Nacional, Argentina). It automates academic manuscript review using **deterministic structural validation** and **selective AI-powered analysis**.

**Current Version:** v0.95 (Q2 2026)
**Architecture:** Hexagonal Architecture (Domain → Application → Infrastructure)
**LLM Integration:** Ollama (hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS)
**Interface:** Gradio web UI + CLI
**Output Location:** `Documents\Silvina\reports\` (Word report, JSON data)

---

## 🌿 Branch Structure & Development Workflow

```
main                    ← Production branch — stable, merged from dev
silvina_editorial_v095  ← Active development branch ← ALL work goes here
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
git checkout silvina_editorial_v095
cd silvina_editorial
source ../venv312/Scripts/activate  # Windows Git Bash
```

**Primary development machine:** DESKTOP-OE2SEGH (32GB RAM, Ryzen 7 8700G)
**Secondary machine:** DESKTOP-LN7Q8I6 (8GB RAM) — code editing only, no LLM inference

---

## ✨ Key Features

### 🎨 **Gradio Web Interface**
- Drag-and-drop file upload
- Interactive result visualization
- One-click Word/JSON download
- Structured expert feedback panel (8 evaluation fields)
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

**3 Output Files** saved to `C:\Users\[user]\Documents\Silvina\reports\`:
1. **📘 Word Report** (`_analisis.docx`)
2. **📊 JSON Data** (`_analisis.json`)
3. **💬 Feedback File** (`_feedback.json`) — via Gradio

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Web Interface | Gradio |
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
git checkout silvina_editorial_v095
cd silvina_editorial_v095

# 3. Create virtual environment
python -m venv ../venv312
source ../venv312/Scripts/activate  # Windows Git Bash

# 4. Install PyTorch for your hardware (required by Laya), then dependencies
# Option A - CPU (default / any OS / Python 3.12 or 3.14):
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Option B - NVIDIA GPU (CUDA):
# Install the CUDA build from https://pytorch.org/get-started/locally/

# Option C - AMD GPU (ROCm):
# - Linux: pip install torch --index-url https://download.pytorch.org/whl/rocm6.2
# - Windows 11 (Radeon RX 7000 / RDNA 3, e.g. RX 7800 XT / gfx110X, requires Python 3.12):
#   pip install --index-url https://rocm.nightlies.amd.com/v2/gfx110X-all/ torch
#   (Note: Windows ROCm wheels are compiled for Python 3.10-3.13; Python 3.14 falls back to CPU).

pip install -r requirements.txt

# 5. Pull LLM model
ollama pull hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS
```

---

## 🚀 Usage

### Web Interface
```bash
python gradio_app.py
```

### Command Line
```bash
python main.py
```

---

## 📁 Project Structure
```
silvina_editorial_v095/
├── main.py
├── gradio_app.py
├── process_feedback.py
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

### v0.95 (Q2 2026) — Current

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

### v0.95 (Q2 2026) — Active Development
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

### v0.95 → v1.0 (Security & Deployment)
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
**Active branch:** `silvina_editorial_v095`

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

**Last Updated:** July 2026
**Version:** 0.95
**Active Branch:** silvina_editorial_v095
**Status:** Active Development 🚀
