# Feature: Include Tables in the Prompts

- **Feature Name**: `include-tables-in-prompt`
- **File Locator**: `odd/tasks/include-tables-in-prompt.md`
- **Branch**: `feat/include-tables-in-prompt`, from `silvina_editorial_v200`.
- **Commit policy**: one work-unit commit per task, Conventional Commits, with its tests and docs. `version.txt` must never be committed. Push and pull request wait for the user's order.

---

## 1. Origin

The analysis of `sandbox/pack_2/inputs/02_IMRyD_Martinez_Garcia.docx` (2026-10-17, `claude-haiku-5-5`) showed in `data/metrics.db` (`ai_interactions`, analysis `a642b7d6…`) that the prompts are plain text with no table content. `DocxTextAdapter.read_paragraphs` iterates `document.paragraphs`, which python-docx limits to paragraphs outside tables, so only the caption (`Tabla 1. …`) reaches the model. An earlier decision kept tables out; this feature reverses it for the prompts only.

Images are not part of this feature: the prompts carry only the figure captions and no image blocks (10 images in the sample document, none sent).

## 2. Decisions

- **Format**: Markdown tables (header row, `---` separator, one row per line). Chosen because models recognize it natively and it keeps columns aligned.
- **Approach B**: a separate path only for the prompts. `read_paragraphs` stays unchanged, so citations, references, grammar, sections and counts keep seeing the same paragraphs as today.
- **Position**: each table is placed in the body at its original position, between the paragraphs that surround it in the document.
- **Scope of the prompts**: the classification, quality and editorial suitability prompts. All of them read the body.
- **Length limit**: tables do not count toward `ArticleBodyDTO.char_count`, so `ArticleLengthChecker` and the article size classification behave as before. `ArticleBodyDTO.text` is unchanged; a new property carries the text with tables.

## 3. Tasks

- [x] **TASK-01: Read the tables of a document.** New domain port `DocumentTablePort` with `read_tables(path) -> list[DocumentTableDTO]`, a `DocumentTableDTO` holding the rows of cell texts and the position (number of non-empty paragraphs that precede the table, so it aligns with the indexes of `read_paragraphs`), and the adapter `DocxTableAdapter` in `src/infrastructure/adapters/document/`. Merged cells must not repeat their text, nested tables are ignored, empty tables are skipped. Raises the same `DocumentNotFound` and `DocumentUnreadable` as `DocxTextAdapter`. Done: feat in the commit that holds this line. 12 tests pass. On `02_IMRyD_Martinez_Garcia.docx` the adapter finds 1 table at `position=63`, 7 rows, up to 3 columns. A cell merged vertically emits `""` in the continuation rows (extension of the brief). Rows can have fewer cells than the grid after a horizontal merge, so TASK-02 must pad them when rendering. The adapter uses private python-docx attributes (`_tc`, `_Cell`, `_Row`), tied to the installed 1.2.0. The suite has 2 failures and 16 collection errors, all `ModuleNotFoundError` for `markupsafe`, `jinja2`, `uvicorn` and `claude_agent_sdk`, none in the new files.
- [x] **TASK-02: Render a table as Markdown.** Pure domain service `TableMarkdownRenderer` that turns a `DocumentTableDTO` into a Markdown table. Escapes `|` inside a cell and collapses line breaks in a cell to a space. First row is the header. Done: feat in the commit that holds this line. 10 tests pass. Short rows are padded to the widest row; a table without cells renders as an empty string; whitespace runs (including non-breaking spaces) collapse to one space.
- [x] **TASK-03: Carry the tables in the article body.** `ArticleBodyDTO` gets `tables: tuple[BodyTableDTO, ...] = ()` (default keeps its 43 callers valid) and a property `text_with_tables`. `ArticleBodyLocator` keeps only the tables whose position falls inside the body span and expresses their position relative to the body paragraphs. `DocumentContentExtractor` reads the tables through the new port and passes them to the locator. `text` and `char_count` do not change. Done: feat in the commit that holds this line. 21 new tests; `src` and `tests` give 2000 passed with the same 2 failures and 20 collection errors as before (missing `markupsafe`, `jinja2`, `uvicorn`, `claude_agent_sdk`). `DocumentContentExtractor` takes the table port and the renderer, so the wiring already builds them. On `02_IMRyD_Martinez_Garcia.docx` the table sits at body position 50, between the two paragraphs of its caption and the source line. A table whose position falls outside the body paragraphs is dropped silently by `text_with_tables`; the locator never produces one. The positions rely on `read_paragraphs`, `DocxTableAdapter` and `ParagraphContentAdapter` counting the same non-blank paragraphs, which nothing enforces.
- [ ] **TASK-04: Send the tables to the prompts.** `QualityAnalyzer` (`body.text` today) and `ArticleClassifier` (`" ".join(body.paragraphs)` today) use `text_with_tables` for the prompt text; the size classification keeps `char_count`. Wire `DocxTableAdapter` in `AnalyzeDocumentUseCaseWiring` and the test doubles.
- [ ] **TASK-05: Verify on the sample.** Run the full suite and `02_IMRyD_Martinez_Garcia.docx`; check in `ai_interactions` that the prompts contain the Markdown table in the right position, that `Tabla 1.` caption and table appear together, and that word and citation counts do not change. Update the docs that describe what the prompts contain.

## 4. Risks

- Prompts grow by the size of the tables; the length limit does not see them. Check the largest sample documents.
- Wide tables (more than 8 columns) or merged cells degrade as Markdown; a record format (`Fila 1: columna=valor`) is the fallback if the sample shows it.
