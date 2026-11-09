"""Reproducible descriptive ranking comparisons; never uses synthetic truth labels."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
from time import perf_counter

from productlens.embeddings import MODEL_ID, MODEL_REVISION
from productlens.grouping import GroupingConfig, group_feedback
from productlens.ingestion import read_feedback, validate_feedback
from productlens.scoring import (DEFAULT_WEIGHTS, FACTORS, METHODS, aggregate_evidence, compare_scores,
                                 score_opportunities, segment_representation)

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {"balanced": DEFAULT_WEIGHTS,
             "enterprise": dict(zip(FACTORS, (.1, .6, .1, .2))),
             "reach": dict(zip(FACTORS, (.7, .1, .1, .1)))}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_experiment(input_path, config_path, output_path):
    input_path, config_path, output_path = map(Path, (input_path, config_path, output_path))
    if output_path.exists():
        raise ValueError("Output directory already exists; use a new directory to preserve experiment evidence.")
    config = json.loads(config_path.read_text())
    if (config["model_id"], config["model_revision"]) != (MODEL_ID, MODEL_REVISION):
        raise ValueError("Grouping config model does not match the installed pinned model.")
    validation = validate_feedback(read_feedback(input_path.read_bytes(), input_path.name))
    if not validation.valid:
        raise ValueError("Invalid input: " + "; ".join(validation.errors))
    start = perf_counter()
    groups = group_feedback(validation.data, GroupingConfig(**config["grouping"]))
    grouping_seconds = perf_counter() - start
    start = perf_counter()
    evidence = aggregate_evidence(validation.data, groups.assignments)
    results = {name: score_opportunities(evidence, weights) for name, weights in SCENARIOS.items()}
    primary = results["balanced"].scores
    comparisons = [compare_scores(primary, "priority_score", baseline) for baseline in METHODS[1:]]
    sensitivity = []
    for factor in FACTORS:
        for multiplier in (.8, 1.2):
            weights = DEFAULT_WEIGHTS.copy()
            weights[factor] *= multiplier
            perturbed = score_opportunities(evidence, weights)
            combined = primary[["opportunity_id", "priority_score"]].merge(
                perturbed.scores[["opportunity_id", "priority_score"]].rename(columns={"priority_score": "perturbed"}),
                on="opportunity_id", validate="one_to_one")
            sensitivity.append(dict(factor=factor, multiplier=multiplier, weights=perturbed.weights,
                                    comparison=compare_scores(combined, "priority_score", "perturbed")))
    scenarios = {}
    for name, result in results.items():
        combined = primary[["opportunity_id", "priority_score"]].merge(
            result.scores[["opportunity_id", "priority_score"]].rename(columns={"priority_score": "scenario"}),
            on="opportunity_id", validate="one_to_one")
        scenarios[name] = dict(weights=result.weights, comparison=compare_scores(combined, "priority_score", "scenario"),
                               segments=segment_representation(evidence, result.scores, "priority_score"))
    source_files = ["productlens/scoring.py", "productlens/ranking_experiment.py", "productlens/ingestion.py",
                    "productlens/grouping.py", "productlens/embeddings.py", "docs/SCORING_PROTOCOL.md", "requirements.txt"]
    report = dict(
        protocol="scoring-v1", input_file=str(input_path), input_sha256=digest(input_path),
        grouping_config_sha256=digest(config_path), model_id=MODEL_ID, model_revision=MODEL_REVISION,
        source_sha256={name: digest(ROOT / name) for name in source_files},
        runtime=dict(python=platform.python_version(), platform=platform.platform(),
                     packages={name: importlib.metadata.version(name) for name in ("pandas", "numpy", "scikit-learn", "sentence-transformers", "torch")}),
        grouping_seconds=grouping_seconds, aggregation_scoring_comparison_seconds=perf_counter() - start,
        observations=len(evidence.rows), customers=len(evidence.accounts), candidates=len(primary),
        traceability=dict(assigned_feedback=len(groups.assignments), uploaded_feedback=len(validation.data), coverage=1.0),
        input_warnings=validation.warnings, common_confidence=.5, normalisation=results["balanced"].normalisation,
        method_coverage={method: int(primary[method].notna().sum()) for method in METHODS},
        baseline_comparisons=comparisons, scenarios=scenarios, weight_sensitivity=sensitivity,
        baseline_segments={method: segment_representation(evidence, primary, method) for method in METHODS},
        limits=["Synthetic descriptive comparisons; no ranking ground truth or superiority claim.",
                "Same frozen grouping across all methods; no manual-workflow comparison or measured time saving.",
                "Effort and impact are provisional proxies; missing inputs restrict common comparisons.",
                "Only weight perturbations tested here; grouping/data robustness and user study remain unmeasured."])
    # Validate JSON before creating the destination; do not emit non-standard NaN values.
    encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
    output_path.mkdir(parents=True, exist_ok=False)
    (output_path / "report.json").write_text(encoded)
    (output_path / "grouping_config.json").write_bytes(config_path.read_bytes())
    groups.assignments.to_csv(output_path / "assignments.csv", index=False)
    groups.opportunities.to_csv(output_path / "opportunities.csv", index=False)
    evidence.accounts.to_csv(output_path / "accounts.csv", index=False)
    evidence.subgroups.to_csv(output_path / "subgroup_effort.csv", index=False)
    for name, result in results.items():
        result.scores.to_csv(output_path / f"scores_{name}.csv", index=False)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "config/semantic.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_experiment(args.input, args.config, args.output)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Ranking experiment failed: {exc}\n")
    print(json.dumps({key: report[key] for key in ("observations", "customers", "candidates", "method_coverage", "traceability")}, indent=2))


if __name__ == "__main__":
    main()
