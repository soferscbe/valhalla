import json

import numpy as np
import pytest

from productlens.embeddings import MODEL_ID, MODEL_REVISION, MAX_TOKENS
from productlens.grouping import normalise_text
from productlens.semantic_experiment import tune, evaluate
from productlens.synthetic import generate_dataset, write_dataset


def test_tuning_reads_only_tuning_text_and_freezes_before_evaluation(tmp_path, monkeypatch):
    dataset = generate_dataset()
    bundle = tmp_path / "dataset"
    write_dataset(dataset, bundle)
    calls = []
    def controlled(texts):
        calls.append(list(texts))
        return np.eye(len(texts)), [False] * len(texts)
    monkeypatch.setattr("productlens.grouping.encode_texts", controlled)
    tuning = tmp_path / "tuning"
    tune(bundle, tuning)
    assert len(calls) == 1
    expected = {normalise_text(text) for text in dataset.feedback_for("tuning").feedback_text}
    assert set(calls[0]) == expected
    frozen = json.loads((tuning / "frozen_config.json").read_text())
    assert frozen["selected_on"] == "tuning only"
    assert len(frozen["opportunity_candidates"]) == 5
    assert frozen["model_revision"] == MODEL_REVISION
    assert not (tmp_path / "heldout").exists()
    evaluate(bundle, tuning / "frozen_config.json", tmp_path / "heldout")
    assert len(calls) == 2
    assert set(calls[1]) == {normalise_text(text) for text in dataset.feedback_for("evaluation").feedback_text}
    report = json.loads((tmp_path / "heldout/evaluation.json").read_text())
    assert report["metrics"]["total_rows"] == 250
    assert report["configuration"]["grouping"] == frozen["grouping"]
    with pytest.raises(ValueError, match="new directory"):
        evaluate(bundle, tuning / "frozen_config.json", tmp_path / "heldout")


def test_evaluation_rejects_source_changes_before_reading_data(tmp_path):
    config = tmp_path / "frozen.json"
    config.write_text(json.dumps({"model_id": MODEL_ID, "model_revision": MODEL_REVISION,
                                  "max_tokens": MAX_TOKENS, "source_sha256": {}}))
    with pytest.raises(ValueError, match="Source/runtime changed"):
        evaluate(tmp_path / "nonexistent", config, tmp_path / "result")
