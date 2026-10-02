# Feature: External LLM Debug Adapter

- **Feature Name**: `external-llm-debug-adapter`
- **File Locator**: `odd/tasks/external-llm-debug-adapter.md`
- **Branch**: `feat/external-llm-debug-adapter`
- **TDD Mode**: Enabled (RED -> GREEN -> REFACTOR)
- **TDD Runner**: `.venv/Scripts/python -m pytest src/`
- **Delivery Strategy**: `ask-on-risk`

---

## 1. Objective

In `APP_MODE=DEBUG` the application must be able to use an external LLM instead of the local Ollama model. The provider and its model are chosen in `.env`, separately from the Ollama model. The first external adapter is Claude, through the Claude Agent SDK (`E:\IA\claude-agent-sdk-python`, v0.2.162), using the subscription and not the API. In `APP_MODE=PROD` an external provider is ignored and Ollama is used.

## 2. Confirmed decisions (user, 2026-10-02)

1. **Authentication**: use the credentials of the `claude login` already done on the machine. The adapter passes `env={"ANTHROPIC_API_KEY": ""}` to the SDK so the key is not inherited. The SDK repository does not document that an empty value overrides the key, so this MUST be verified in a real run (see TASK-04). The SDK itself has no subscription/API switch: it spawns the bundled Claude Code CLI and passes the inherited environment (`subprocess_cli.py:819-823`).
2. **Selection**: `LLM_PROVIDER` (`ollama` | `claude`, extensible to other providers) and `EXTERNAL_LLM_MODEL_NAME`, independent from `OLLAMA_MODEL_NAME`. `APP_MODE=PROD` ignores an external provider and uses Ollama. `APP_MODE=DEBUG` with an external provider requires `EXTERNAL_LLM_MODEL_NAME` (fail-fast `ValueError`).
3. **Generation options**: the domain `options` dict (`temperature`, `num_predict`) is Ollama-specific; the Claude adapter ignores it silently (the SDK has no `temperature` or `max_tokens`).
4. **Dependency**: `requirements-debug.txt` (`-r requirements.txt` plus `claude-agent-sdk`). The wiring loads the external adapter lazily with `importlib.import_module` through a `provider -> module` registry, only in DEBUG with an external provider. PROD does not need the SDK. No local imports (project rule).

## 3. Scope

### In scope
- `AiProvider.CLAUDE`.
- `EnvConfig`: `llm_provider` (effective provider, PROD forces Ollama) and `external_llm_model_name`, with the DEBUG fail-fast rule.
- `ClaudeGeneratorAdapter` (infrastructure) implementing `LlmGeneratorPort`, mapping SDK failures to the existing `LanguageModelError` hierarchy.
- Loader/registry in `src/infrastructure/wirings/` and its use in `AnalyzeDocumentUseCaseWiring` (generator, `AiProvider` and model name recorded by `AuditedLlmGeneratorAdapter`).
- `requirements-debug.txt`, `.env.example`, `.env` documentation, README section.

### Out of scope
- Other providers (ChatGPT, Gemini): only the registry makes them additive.
- Real API-key billing path, tools, sessions, streaming.
- Changing domain ports or the prompts.

## 4. Open assumptions to verify (do not infer)

- Keys of `ResultMessage.usage` (`input_tokens`/`output_tokens` are used by SDK tests but the field is an untyped dict): read with `.get`, missing becomes `None`.
- Whether `ANTHROPIC_API_KEY=""` really forces the subscription (TASK-04 real run).
- SDK options chosen for plain text generation: `tools=[]`, `max_turns=1`, `setting_sources=[]` (no CLAUDE.md or settings loaded). Thinking and system prompt are left at SDK defaults.

## 5. Tasks

- [x] **TASK-01** `AiProvider.CLAUDE`, `EnvConfig.llm_provider` / `external_llm_model_name` with PROD-ignores and DEBUG-requires-model rules, tests. Commit `353dab8`; 130 tests green (RED 13 failing first), ruff clean.
- [x] **TASK-02** `ClaudeGeneratorAdapter` with unit tests using a fake of the SDK `query` (no network), error mapping, sync bridge over the async SDK. 18 tests (RED 18 failing first), whole suite 1026 passed, ruff clean. Errors: the ClaudeSDKError hierarchy, AssistantMessage.error and ResultMessage.is_error map to LanguageModelUnavailable; no LanguageModelNotFound mapping because the SDK does not expose an unknown-model error. Follow-up: Claude stop_reason values (end_turn, max_tokens) are stored raw and do not match LlmDoneReason.LENGTH, so the truncation warning will not fire for Claude.
- [x] **TASK-03** External generator loader (registry + `import_module`) and `AnalyzeDocumentUseCaseWiring` selection by `EnvConfig`; wiring tests. Whole suite 1037 passed, ruff clean. `LanguageModelBackendNotInstalled` added for a missing SDK. Not covered: a test that the loader and wiring modules do not import `claude_agent_sdk` (the claude adapter test imports it earlier in the same pytest process, so `sys.modules` is unreliable).
- [x] **TASK-04** `requirements-debug.txt` and README done. `.env.example` and `.env` NOT edited: the Gentle AI safety policy blocks writes to those paths; the user must add the `LLM_PROVIDER` and `EXTERNAL_LLM_MODEL_NAME` block by hand. Real run (2026-10-02, `claude-haiku-4-5-20251001`, SDK 0.2.162 from PyPI): with a bogus `ANTHROPIC_API_KEY` in the process environment the adapter returned `OK` (928 prompt tokens, 42 completion tokens, `done_reason=end_turn`) through the subscription; the control without the override printed "ANTHROPIC_API_KEY or another auth source is set and takes precedence over your claude.ai login" and never completed. So `ANTHROPIC_API_KEY=""` does force the subscription in this CLI version.

## 6. Evidence

(commit identities and observed checks are recorded here per task)
