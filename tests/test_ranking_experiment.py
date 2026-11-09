import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from productlens.embeddings import MODEL_ID, MODEL_REVISION
from productlens.grouping import group_feedback
from productlens.ranking_experiment import run_experiment


def test_experiment_is_reproducible_and_preserves_outputs(tmp_path, monkeypatch):
    # Real aggregation/scoring, controlled identity embeddings only to keep this unit test offline.
    monkeypatch.setattr("productlens.ranking_experiment.group_feedback", lambda data, config:
        group_feedback(data, config, lambda texts: (np.eye(len(texts)), [False] * len(texts))))
    input_path = Path(__file__).resolve().parents[1] / "data/sample_feedback.csv"
    config = tmp_path / "config.json"
    config.write_text(json.dumps(dict(model_id=MODEL_ID, model_revision=MODEL_REVISION,
                                     grouping=dict(opportunity_similarity=.7, duplicate_similarity=.9))))
    output = tmp_path / "first"
    report = run_experiment(input_path, config, output)
    assert report["observations"] == 6 and report["traceability"]["coverage"] == 1
    assert len(report["baseline_comparisons"]) == 3 and len(report["weight_sensitivity"]) == 8
    assert set(report["scenarios"]) == {"balanced", "enterprise", "reach"}
    assert json.loads((output / "report.json").read_text())["input_sha256"] == report["input_sha256"]
    with pytest.raises(ValueError, match="already exists"):
        run_experiment(input_path, config, output)
    second = tmp_path / "second"
    run_experiment(input_path, config, second)
    for path in output.glob("*.csv"):
        assert path.read_bytes() == (second / path.name).read_bytes()
    assert len(pd.read_csv(output / "scores_balanced.csv")) == 6


def test_wrong_model_rejected_before_writing(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps(dict(model_id="wrong", model_revision=MODEL_REVISION)))
    with pytest.raises(ValueError, match="model"):
        run_experiment(tmp_path / "absent.csv", config, tmp_path / "out")
    assert not (tmp_path / "out").exists()
