"""Separate tuning and held-out evaluation commands; no evaluation-based search."""

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import resource
import time

import pandas as pd

from productlens.embeddings import MODEL_ID, MODEL_REVISION, MAX_TOKENS
from productlens.grouping import GroupingConfig, group_prepared, prepare_feedback, normalise_text
from productlens.grouping_metrics import clustering_metrics
from productlens.ingestion import read_feedback

OPPORTUNITY_GRID = (0.20, 0.30, 0.40, 0.50, 0.60)
DUPLICATE_GRID = (0.55, 0.65, 0.75, 0.85)
SOURCE_FILES = ("embeddings.py", "grouping.py", "grouping_metrics.py", "semantic_experiment.py")


def source_hashes():
    return {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() for name in SOURCE_FILES}


def runtime_versions():
    return {name: importlib.metadata.version(name) for name in
            ("sentence-transformers", "transformers", "torch", "scikit-learn", "numpy", "pandas")}


def _read(dataset: Path, split: str):
    manifest = json.loads((dataset / "manifest.json").read_text())
    for name in (f"inputs/{split}.csv", "truth/labels.csv"):
        if hashlib.sha256((dataset / name).read_bytes()).hexdigest() != manifest["files_sha256"][name]:
            raise ValueError(f"Dataset hash mismatch: {name}")
    frame = read_feedback((dataset / f"inputs/{split}.csv").read_bytes(), "feedback.csv")
    labels = pd.read_csv(dataset / "truth/labels.csv", keep_default_na=False)
    labels = labels[labels.split == split].copy()
    if not labels.feedback_id.is_unique or set(frame.feedback_id) != set(labels.feedback_id):
        raise ValueError("Split labels must match input IDs exactly.")
    evidence = frame.merge(labels, on="feedback_id", validate="one_to_one")
    return frame, evidence, manifest


def _write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def tune(dataset: Path, output: Path):
    if output.exists():
        raise ValueError("Experiment output must be a new directory.")
    frame, evidence, manifest = _read(dataset, "tuning")
    started = time.perf_counter()
    prepared = prepare_feedback(frame)  # No labels or business signals reach encoder.
    encoding_seconds = time.perf_counter() - started
    candidates = []
    for broad in OPPORTUNITY_GRID:
        prediction = group_prepared(prepared, GroupingConfig(broad, 0.85))
        metrics = clustering_metrics(evidence, prediction.assignments)
        candidates.append({"opportunity_similarity": broad, "unique_text_theme_ari": metrics["unique_texts"]["theme_ari"]})
    best_broad = max(candidates, key=lambda c: (c["unique_text_theme_ari"], c["opportunity_similarity"]))["opportunity_similarity"]
    duplicate_candidates = []
    for strict in DUPLICATE_GRID:
        if strict < best_broad:
            continue
        prediction = group_prepared(prepared, GroupingConfig(best_broad, strict))
        metrics = clustering_metrics(evidence, prediction.assignments)
        duplicate_candidates.append({"duplicate_similarity": strict,
                                     "unique_text_duplicate_f1": metrics["unique_texts"]["duplicate_pairs"]["f1"]})
    best_strict = max(duplicate_candidates, key=lambda c: (c["unique_text_duplicate_f1"] if c["unique_text_duplicate_f1"] is not None else -1,
                                                         c["duplicate_similarity"]))["duplicate_similarity"]
    config = GroupingConfig(best_broad, best_strict)
    frozen = {
        "protocol": "semantic-v1", "selected_on": "tuning only",
        "model_id": MODEL_ID, "model_revision": MODEL_REVISION, "max_tokens": MAX_TOKENS,
        "grouping": asdict(config), "dataset_content_sha256": manifest["content_sha256"],
        "input_sha256": manifest["files_sha256"]["inputs/tuning.csv"],
        "objective": "Maximise unique-normalised-text theme ARI, then unique-text duplicate pair F1; each tie chooses higher similarity. No held-out search.",
        "opportunity_candidates": candidates, "duplicate_candidates": duplicate_candidates,
        "source_sha256": source_hashes(), "runtime": runtime_versions(),
    }
    prediction = group_prepared(prepared, config)
    output.mkdir(parents=True)
    _write_json(output / "frozen_config.json", frozen)
    _write_json(output / "tuning_metrics.json", {"metrics": clustering_metrics(evidence, prediction.assignments),
                                               "encoding_and_load_seconds": encoding_seconds})
    prediction.assignments.to_csv(output / "assignments.csv", index=False)
    print(json.dumps({"phase": "tuning", "grouping": asdict(config), "output": str(output.resolve())}))


def evaluate(dataset: Path, frozen_path: Path, output: Path):
    if output.exists():
        raise ValueError("Experiment output must be a new directory.")
    frozen = json.loads(frozen_path.read_text())
    if (frozen["model_id"], frozen["model_revision"], frozen["max_tokens"]) != (MODEL_ID, MODEL_REVISION, MAX_TOKENS):
        raise ValueError("Frozen model configuration differs from current implementation.")
    if frozen["source_sha256"] != source_hashes() or frozen["runtime"] != runtime_versions():
        raise ValueError("Source/runtime changed after tuning; preserve the frozen implementation or create a new declared run.")
    frame, evidence, manifest = _read(dataset, "evaluation")
    if frozen["dataset_content_sha256"] != manifest["content_sha256"]:
        raise ValueError("Evaluation must use the same versioned dataset bundle as tuning.")
    config = GroupingConfig(**frozen["grouping"])
    started = time.perf_counter()
    prepared = prepare_feedback(frame)
    encoded = time.perf_counter()
    prediction = group_prepared(prepared, config)
    grouped = time.perf_counter()
    metrics = clustering_metrics(evidence, prediction.assignments)
    joined = evidence.merge(prediction.assignments, on="feedback_id", validate="one_to_one")
    challenge = joined[joined.label_kind != "clear"].copy()
    clear_themes = joined[joined.label_kind == "clear"].groupby("opportunity_id").primary_theme.agg(lambda values: "|".join(sorted(set(values))))
    challenge["clear_themes_in_same_group"] = challenge.opportunity_id.map(clear_themes).fillna("")
    unique = joined[joined.label_kind == "clear"].copy()
    unique["normalised_text"] = unique.feedback_text.map(normalise_text)
    unique = unique.drop_duplicates("normalised_text")
    # Compact, reproducible evidence examples of both missed and false duplicate links.
    errors = []
    rows = list(unique.itertuples())
    for i, left in enumerate(rows):
        for right in rows[i + 1:]:
            same = left.duplicate_group == right.duplicate_group
            proposed = left.duplicate_group_id == right.duplicate_group_id
            if same != proposed:
                errors.append({"left_id": left.feedback_id, "right_id": right.feedback_id,
                               "left_text": left.feedback_text, "right_text": right.feedback_text,
                               "error": "missed_duplicate" if same else "false_duplicate"})
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_mib = peak / (1024**2 if platform.system() == "Darwin" else 1024)
    report = {
        "protocol": frozen["protocol"], "split": "evaluation", "configuration": frozen,
        "frozen_config_sha256": hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
        "metrics": metrics, "challenge_counts": challenge.label_kind.value_counts().to_dict(),
        "opportunity_count_all_rows": len(prediction.opportunities),
        "truncated_rows": int(prediction.assignments.text_truncated.sum()),
        "timing_seconds": {"load_and_encode": encoded - started, "group_and_summarise": grouped - encoded},
        "peak_process_rss_mib": peak_mib, "platform": platform.platform(),
        "python": platform.python_version(), "device": "cpu", "torch_threads": 2,
        "timing_caveat": "Single local run including cached model load; not a productivity benchmark or cloud resource guarantee.",
    }
    output.mkdir(parents=True)
    _write_json(output / "evaluation.json", report)
    prediction.assignments.to_csv(output / "assignments.csv", index=False)
    prediction.opportunities.to_csv(output / "opportunities.csv", index=False)
    challenge.to_csv(output / "challenge_review.csv", index=False)
    pd.DataFrame(errors, columns=["left_id", "right_id", "left_text", "right_text", "error"]).to_csv(output / "duplicate_errors.csv", index=False)
    print(json.dumps({"phase": "evaluation", "metrics": metrics, "output": str(output.resolve())}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Tune once on tuning data; evaluate frozen grouping settings separately.")
    parser.add_argument("phase", choices=["tune", "evaluate"])
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frozen", type=Path)
    args = parser.parse_args()
    if args.phase == "evaluate" and args.frozen is None:
        parser.error("evaluate requires --frozen")
    if args.phase == "tune":
        tune(args.dataset, args.output)
    else:
        evaluate(args.dataset, args.frozen, args.output)


if __name__ == "__main__":
    main()
