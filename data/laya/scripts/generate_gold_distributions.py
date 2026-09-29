"""Generate Laya teacher gold probability distributions via repeated Ollama sampling."""

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import ollama

REPO_ROOT = Path(__file__).resolve().parents[3]
QUESTIONS_PATH = (
    REPO_ROOT / "src" / "infrastructure" / "resources" / "laya" / "decision_questions.json"
)
DEFAULT_MODEL = "hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS"
DEFAULT_BASE_URL = "http://localhost:11434"


def load_questions(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error loading questions from {path}: {e}")
        sys.exit(1)


def build_prompt(state: str, questions: dict) -> str:
    lines = [
        "Eres un editor experto evaluando artículos académicos de defensa.",
        "Leé el texto y respondé cada pregunta eligiendo EXACTAMENTE una opción.",
        "Devolvé SOLO un objeto JSON con las claves exactas listadas abajo, sin texto adicional ni explicaciones.",
        "",
        "TEXTO:",
        state,
        "",
        "PREGUNTAS Y OPCIONES:",
    ]
    for qid, q in questions.items():
        if q["type"] == "score":
            levels = "; ".join(f"{i}={desc}" for i, desc in enumerate(q["criteria"]))
            lines.append(f"- {qid} ({q['instructions']}): elegí un entero 0-10. Niveles: {levels}")
        else:
            options = "; ".join(f"{k}={v}" for k, v in q["criteria"].items())
            lines.append(f"- {qid} ({q['instructions']}): opciones: {options}")
    lines.append("")
    lines.append("JSON:")
    return "\n".join(lines)


def parse_response(text: str, questions: dict) -> dict | None:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None

    answers = {}
    for qid, q in questions.items():
        if qid not in data:
            return None
        if q["type"] == "score":
            try:
                level = int(data[qid])
            except (TypeError, ValueError):
                return None
            if not 0 <= level <= len(q["criteria"]) - 1:
                return None
            answers[qid] = level
        else:
            value = str(data[qid]).strip().upper()
            if value not in q["criteria"]:
                return None
            answers[qid] = value
    return answers


def sample_gold(
    client: ollama.Client,
    model: str,
    state: str,
    questions: dict,
    repeats: int,
    temperature: float,
) -> tuple[dict, int]:
    votes = {qid: Counter() for qid in questions}
    prompt = build_prompt(state, questions)
    valid_samples = 0

    for _ in range(repeats):
        response = client.generate(model=model, prompt=prompt, options={"temperature": temperature})
        answers = parse_response(response.get("response", ""), questions)
        if answers is None:
            continue
        valid_samples += 1
        for qid, value in answers.items():
            votes[qid][value] += 1

    gold = {}
    for qid, q in questions.items():
        counter = votes[qid]
        total = sum(counter.values())
        if q["type"] == "score":
            keys = [str(i) for i in range(len(q["criteria"]))]
            key_lookup = {k: int(k) for k in keys}
        else:
            keys = list(q["criteria"].keys())
            key_lookup = {k: k for k in keys}

        if total == 0:
            probabilities = {k: 1.0 / len(keys) for k in keys}
        else:
            probabilities = {k: counter.get(key_lookup[k], 0) / total for k in keys}
        gold[qid] = {"probabilities": probabilities}

    return gold, valid_samples


def main():
    parser = argparse.ArgumentParser(
        description="Generate teacher gold distributions for Laya via Ollama repeated sampling"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Input JSONL (state/questions/expected)"
    )
    parser.add_argument("--output", type=Path, required=True, help="Output JSONL with gold added")
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--base-url", type=str, default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--repeats", type=int, default=5, help="Samples per item to build the distribution"
    )
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--offset", type=int, default=0, help="Skip this many input lines")
    parser.add_argument("--limit", type=int, default=None, help="Process at most this many lines")
    args = parser.parse_args()

    questions = load_questions(args.questions)
    client = ollama.Client(host=args.base_url)

    try:
        with open(args.input, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"Error reading input {args.input}: {e}")
        sys.exit(1)
    end = args.offset + args.limit if args.limit else None
    selected = lines[args.offset : end]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_f = open(args.output, "w", encoding="utf-8")
    except OSError as e:
        print(f"Error opening output path {args.output}: {e}")
        sys.exit(1)

    with out_f:
        for i, line in enumerate(selected):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Skipping malformed line {args.offset + i}: {e}")
                continue
            start = time.time()
            gold, valid_samples = sample_gold(
                client, args.model, record["state"], questions, args.repeats, args.temperature
            )
            elapsed = time.time() - start
            record["gold"] = gold
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()
            print(
                f"[{i + 1}/{len(selected)}] valid_samples={valid_samples}/{args.repeats} elapsed={elapsed:.1f}s"
            )


if __name__ == "__main__":
    main()
