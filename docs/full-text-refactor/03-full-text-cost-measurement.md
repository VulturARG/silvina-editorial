# Token and Latency Cost of Full-Text Input (TASK-02)

- **Branch**: `silvina_editorial_v200`
- **Date**: 2026-10-15
- **Status**: Measurement from `data/metrics.db` (read-only). The controlled run was skipped by the user (section 6); latency is not conclusive.
- **Related**: `odd/tasks/full-text-analysis-refactor-study.md`, `docs/full-text-refactor/02-text-limits-inventory.md`

## 1. Data used

- Source: tables `analyses`, `stage_durations` and `ai_interactions` of `data/metrics.db`, opened read-only.
- Filter: analyses with `status = success` and a total duration of at least 30 s, to discard test rows. 41 analyses remain.
- The comparison uses the two documents of about 50k characters analyzed since 2026-10-14, with Claude Haiku 4.5 and Ollama `gemma4-26b-adapted` (5 calls each):
  - `01_IMRyD_Cano_Martinez.docx` (51013 characters, 7448 words);
  - `01_IMRyD_Gomez_Rubio.docx` (53431 characters, 8385 words, only with the old 32000 limit).
- Two "before" runs and one "after" run per provider on Cano Martinez:
  - **Before** (quality limit 32000): Haiku 2026-10-15 03:56, Gemma 2026-10-15 03:59.
  - **After** (quality limit 75000, whole document): Haiku 2026-10-15 11:54, Gemma 2026-10-15 12:21.
- The prompt size confirms which limit was active: quality prompts of about 33.4k characters before and 50.3k after.

## 2. Prompt size per call

Characters of `input_payload` and prompt tokens reported by the backend (Cano Martinez).

| Call | Chars before | Chars after | Gemma tokens before | Gemma tokens after | Haiku tokens before | Haiku tokens after |
| --- | --- | --- | --- | --- | --- | --- |
| Classification | 43781 | 43781 | 9100 | 9100 | 12834 | 12834 |
| Quality 1 | 33433 | 50335 | 6967 | 11557 | 10048 | 15356 |
| Quality 2 | 33475 | 50377 | 6988 | 11578 | 10055 | 15363 |
| Suitability contribution | 33195 | 50097 | 6878 | 11468 | 9926 | 15234 |
| Suitability alignment | 35074 | 51976 | 7242 | 11832 | 10456 | 15764 |
| **Total** | 178958 | 246566 | 37175 | 55535 | 53319 | 74551 |

Classification did not change because its limit was already raised before and it strips the bibliography.

Only the four quality calls changed (+50 % characters each). In total, characters grow 38 %, Gemma prompt tokens 49 % and Haiku prompt tokens 40 %. Gemma grows more than the characters because the added text includes the bibliography, which is denser in tokens (section 3).

## 3. Characters per token

| Prompt | Gemma | Haiku |
| --- | --- | --- |
| Quality 1 (whole document, with bibliography) | 4.36 | 3.28 |
| Classification (body without bibliography) | 4.81 | 3.41 |

Haiku counts about 1000 more tokens per call than Gemma (the Agent SDK adds a fixed overhead), which lowers its ratio.

The bibliography is denser in tokens. Comparing the quality prompt with the classification prompt, 6554 more characters cost 2457 more tokens in Gemma and 2522 in Haiku, about 2.6 to 2.7 characters per token against 4.4 to 4.8 for the body. This is an approximation: the two templates differ.

Consequence: in the whole-document quality prompt the bibliography is about 13 % of the characters and about 21 % of the Gemma tokens.

## 4. Latency

Totals per analysis (seconds), same document.

| Run | Total | LLM time | Classification | Quality and suitability | Grammar |
| --- | --- | --- | --- | --- | --- |
| Haiku before | 68.1 | 61.1 | 7.0 | 54.1 | 3.5 |
| Haiku after | 136.1 | 125.8 | 6.9 | 118.9 | 7.5 |
| Gemma before (03:02) | 160.7 | 154.0 | 20.1 | 134.0 | 4.3 |
| Gemma before (03:59) | 177.7 | 171.2 | 23.1 | 148.1 | 3.2 |
| Gemma after | 104.4 | 98.2 | 2.0 | 96.3 | 3.1 |

Reading:

- **Haiku**: the first quality call took 68.6 s in the "after" run against 19 to 24 s in every other run. Replacing that call by a typical 21 s, the "after" analysis would take about 88 s, which is still about 20 s above the "before" runs. Part of that gap is the larger prompts and the longer suitability output (975 tokens in one call against about 210 before). One outlier is a large part of the comparison, so the size of the Haiku slowdown cannot be fixed from a single sample.
- **Gemma**: the "after" run is the fastest of the series even though it processed 49 % more tokens. The classification call took 2.0 s against 20 to 40 s in the other runs for the same prompt, and the second quality call took 11.4 s. These two signs point to a loaded model and a prompt cache hit, not to the cost of the text. Latency between Gemma runs varies by a factor of two or more for identical inputs (160 to 234 s for the same prompts), so the data cannot isolate the cost of 50 % more text.
- **Grammar** stays between 3 and 8 s: it still checks only the first 20 paragraphs.

What the data does show: the time per call does not grow with the characters in a way that is visible above the noise. What it does not show: the prefill cost of the extra tokens under comparable conditions.

## 5. Cost and context

**Haiku 4.5 cost**, assuming 1 USD per million input tokens and 5 USD per million output tokens and counting all prompt tokens at the base price (an upper bound; the data does not say whether any tokens were cached).

| Run | Input tokens | Output tokens | Estimated cost |
| --- | --- | --- | --- |
| Before | 53319 | 3307 | 0.070 USD |
| After | 74551 | 4259 | 0.096 USD |

The increase is about 37 %. The price assumption comes from the notes of an earlier session and was not re-verified.

**Gemma context.** `OLLAMA_NUM_CTX` is 24576.

- Largest observed prompt: 11832 tokens (48 % of the context).
- Extrapolating linearly at 4.36 characters per token, a prompt at the 75000 limit would be about 17.3k tokens (70 %), plus up to about 700 output tokens.
- If a document were dense like a bibliography (2.7 characters per token), 75000 characters would be about 27.8k tokens, above the context. This is a theoretical worst case, not observed. No code ties the character limit to the context window (see the inventory, finding 5).

## 6. Controlled run: skipped

The data above mixes server state, model load and API variance. A controlled run would have repeated the same document under stable conditions. On 2026-10-15 the user decided to skip it because it is not relevant for the planned refactor. The design proceeds with the token and cost figures above and treats latency as unmeasured.

## 7. Limits of this measurement

- One document with 50k characters per provider and condition (n = 1 per cell).
- Ollama latency is not reproducible between runs; the cause was not diagnosed here.
- Token counts differ per backend and Haiku includes SDK overhead.
- Cost uses an assumed price and ignores caching.
- All 41 successful analyses in `metrics.db` last at least 30 s, so no test row is among them; the 13 error rows and the 1 running row were not used.
