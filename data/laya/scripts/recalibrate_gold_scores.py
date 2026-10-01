"""Recalibrate Laya gold score distributions using expected ground truth without compression."""

import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLD_DIR = REPO_ROOT / "data" / "laya" / "gold"
SCORE_KEYS = [
    "score_clarity",
    "score_coherence",
    "score_argumentation",
    "score_conclusions",
]


def calibrated_distribution(
    target: float, sigma: float = 0.8, n_levels: int = 11
) -> dict[str, float]:
    """Generate a discrete normal distribution centered on target with sum(p)=1 and E[X]=target."""

    def compute_mean_and_weights(center: float) -> tuple[float, list[float]]:
        weights = [math.exp(-0.5 * ((i - center) / sigma) ** 2) for i in range(n_levels)]
        total = sum(weights)
        probs = [w / total for w in weights]
        mean = sum(i * p for i, p in enumerate(probs))
        return mean, probs

    low = max(0.0, target - 2.0)
    high = min(float(n_levels - 1), target + 2.0)
    best_probs = None
    for _ in range(40):
        mid = (low + high) / 2.0
        mean, probs = compute_mean_and_weights(mid)
        best_probs = probs
        if mean < target:
            low = mid
        else:
            high = mid

    assert best_probs is not None
    # Round to 5 decimal places and re-normalize so sum is exactly 1.0
    rounded = [round(p, 5) for p in best_probs]
    total = sum(rounded)
    rounded[int(round(target))] += round(1.0 - total, 5)

    return {str(i): round(p, 5) for i, p in enumerate(rounded)}


def process_file(file_path: Path) -> tuple[int, dict[str, float]]:
    print(f"Processing {file_path.name}...")
    updated_lines = []
    score_means: dict[str, list[float]] = {k: [] for k in SCORE_KEYS}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as err:
                    print(f"Skipping malformed line in {file_path}: {err}")
                    continue
                expected = row["expected"]
                gold = row["gold"]

                for key in SCORE_KEYS:
                    target_score = float(expected[key])
                    dist = calibrated_distribution(target_score)
                    gold[key] = {"probabilities": dist}
                    calculated_mean = sum(int(idx) * prob for idx, prob in dist.items())
                    score_means[key].append(calculated_mean)

                updated_lines.append(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as err:
        print(f"Error reading {file_path}: {err}")
        return 0, {}

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
    except OSError as err:
        print(f"Error writing {file_path}: {err}")
        return 0, {}

    avg_means = {k: sum(v) / len(v) for k, v in score_means.items()}
    return len(updated_lines), avg_means


def main():
    splits = [
        "train_with_gold.jsonl",
        "calibration_with_gold.jsonl",
        "test_with_gold.jsonl",
    ]
    for split in splits:
        path = GOLD_DIR / split
        count, avg_means = process_file(path)
        print(f"  [OK] {split}: {count} records updated")
        for k, v in avg_means.items():
            print(f"    - {k} average mean: {v:.2f}")


if __name__ == "__main__":
    main()
