# Agent Instructions

Before reading, writing, or reviewing any file under `src/`, `.agent/skills/clean-architecture/SKILL.md` MUST be read and followed strictly.

## Key Clean Architecture Invariants

- **Layer import direction (strict & unidirectional)**: Dependencies flow inward toward `domain/`. `domain/` depends only on Python standard library and domain modules; `application/` depends only on `domain/`; `infrastructure/` can depend on all layers and external frameworks. Never import outer layers from inner layers.
- **No inline comments**: Do not write inline (`#`) comments in production code. Identifiers, functions, and class structures must be self-explanatory, with PEP 257 docstrings on public classes and methods.
- **Testing with unittest.TestCase**: All tests MUST inherit from `unittest.TestCase`. Domain tests must run as pure Python without external services or network calls.
- **Wirings assemble adapters**: Concrete infrastructure adapters are instantiated and wired only in `src/infrastructure/wirings/` (or test doubles in `src/infrastructure/tests/test_doubles/`), never inside use cases or domain services.
- **Error handling boundary**: The `@generic_error_handler` decorator goes ONLY on the public entry method of use cases, never on domain services, entities, or adapters.

## Code Exploration

- **CodeGraph first**: To explore or understand code under `src/`, call `codegraph_explore` (MCP tool `mcp__codegraph__codegraph_explore`, or the `codegraph` tool) BEFORE `grep`, `read`, or `bash`. It returns verbatim source, call relationships, and blast radius; do not re-read the files it already returned.
- **Query by symbol names**: Use class, method, or function names (e.g. `QualityTextSampler build_sample`). Environment variable names and string literals are not indexed as symbols and will not be found this way.
- **Fall back to `grep`/`read`** only for what the graph does not cover: environment variables and `.env` keys, string literals, non-Python files (Modelfiles, prompts, docs), logs, and a single known line range.
- **Before editing**, check the blast radius of the symbols to change and update the callers and tests it lists.
