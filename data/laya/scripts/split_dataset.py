"""Stratified dataset partitioner for Silvina Editorial decisions in Laya.

Splits dataset_raw.jsonl into:
  - train.jsonl (80% = 384 samples)
  - calibration.jsonl (10% = 48 samples, strictly held out for L-BFGS temperature scaling)
  - test.jsonl (10% = 48 samples, blind evaluation for laya-evals)

Uses a fixed random seed (42) and stratified sampling by archetype tag.
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

DEFAULT_INPUT_PATH = Path("E:/IA/laya/data/silvina_editorial/dataset_raw.jsonl")
DEFAULT_DATA_DIR = Path("E:/IA/laya/data/silvina_editorial")


def partition_dataset(input_file: Path, output_dir: Path, seed: int = 42):
    random.seed(seed)

    if not input_file.is_file():
        raise FileNotFoundError(f"Input dataset not found: {input_file}")

    # Group samples by primary tag (archetype or ood category)
    grouped_samples = defaultdict(list)
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            # Find primary group key
            tags = item.get("tags", [])
            group_key = tags[0] if tags else "unknown"
            grouped_samples[group_key].append(item)

    print(
        f"Loaded {sum(len(v) for v in grouped_samples.values())} samples across {len(grouped_samples)} groups."
    )

    train_set = []
    calibration_set = []
    test_set = []

    # Shuffle within each group deterministically
    groups = list(grouped_samples.keys())
    groups.sort()  # deterministic group order

    # We need exactly 48 calibration and 48 test samples from 60 groups (each group has 8 samples)
    # Shuffle the group keys to randomly choose which 48 groups contribute to calibration and test
    shuffled_groups = list(groups)
    random.shuffle(shuffled_groups)
    calib_groups = set(shuffled_groups[:48])

    random.shuffle(shuffled_groups)
    test_groups = set(shuffled_groups[:48])

    for g_key in groups:
        samples = list(grouped_samples[g_key])
        random.shuffle(samples)

        calib_item = samples.pop() if g_key in calib_groups else None
        test_item = samples.pop() if g_key in test_groups else None

        if calib_item:
            calibration_set.append(calib_item)
        if test_item:
            test_set.append(test_item)

        train_set.extend(samples)

    # Assert exact sizes
    assert len(train_set) == 384, f"Expected 384 train samples, got {len(train_set)}"
    assert len(calibration_set) == 48, (
        f"Expected 48 calibration samples, got {len(calibration_set)}"
    )
    assert len(test_set) == 48, f"Expected 48 test samples, got {len(test_set)}"
    assert len(train_set) + len(calibration_set) + len(test_set) == 480, "Sum of splits != 480"

    # Write files
    train_path = output_dir / "train.jsonl"
    calib_path = output_dir / "calibration.jsonl"
    test_path = output_dir / "test.jsonl"

    for path, dataset, name in [
        (train_path, train_set, "Train (80%)"),
        (calib_path, calibration_set, "Calibration (10%)"),
        (test_path, test_set, "Test (10%)"),
    ]:
        with open(path, "w", encoding="utf-8") as f:
            for s in dataset:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"Wrote {len(dataset)} samples to {path} ({name})")

    # Verify no state collision / leak between splits
    train_states = {s["state"] for s in train_set}
    calib_states = {s["state"] for s in calibration_set}
    test_states = {s["state"] for s in test_set}

    assert not (train_states & calib_states), "Data leak detected: train and calibration overlap!"
    assert not (train_states & test_states), "Data leak detected: train and test overlap!"
    assert not (calib_states & test_states), "Data leak detected: calibration and test overlap!"

    print(
        "\nData integrity check: 100% DISJOINT SPLITS (zero overlap between train, calibration, and test)."
    )
    print("Stratified partition completed successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Split dataset_raw.jsonl into train/calibration/test splits"
    )
    parser.add_argument(
        "--input", type=Path, default=DEFAULT_INPUT_PATH, help="Path to dataset_raw.jsonl"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_DATA_DIR, help="Directory to save splits"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    partition_dataset(args.input, args.output_dir, args.seed)


if __name__ == "__main__":
    main()
