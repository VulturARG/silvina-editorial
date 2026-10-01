# Agent Instructions

Before reading, writing, or reviewing any file under `src/`, `.agent/skills/clean-architecture/SKILL.md` MUST be read and followed strictly.

## Key Clean Architecture Invariants

- **Layer import direction (strict & unidirectional)**: Dependencies flow inward toward `domain/`. `domain/` depends only on Python standard library and domain modules; `application/` depends only on `domain/`; `infrastructure/` can depend on all layers and external frameworks. Never import outer layers from inner layers.
- **No inline comments**: Do not write inline (`#`) comments in production code. Identifiers, functions, and class structures must be self-explanatory, with PEP 257 docstrings on public classes and methods.
- **Testing with unittest.TestCase**: All tests MUST inherit from `unittest.TestCase`. Domain tests must run as pure Python without external services or network calls.
- **Wirings assemble adapters**: Concrete infrastructure adapters are instantiated and wired only in `src/infrastructure/wirings/` (or test doubles in `src/infrastructure/tests/test_doubles/`), never inside use cases or domain services.
- **Error handling boundary**: The `@generic_error_handler` decorator goes ONLY on the public entry method of use cases, never on domain services, entities, or adapters.
