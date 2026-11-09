import hashlib
import json
import subprocess
import sys

import pandas as pd
import pytest

from productlens.ingestion import OPTIONAL, REQUIRED, read_feedback, validate_feedback
from productlens.synthetic import (
    END_DATE, START_DATE, GenerationConfig, assert_integrity, generate_dataset, write_dataset,
)
from productlens.synthetic_catalog import FAMILIES


@pytest.fixture(scope="module")
def dataset():
    return generate_dataset()


@pytest.mark.parametrize("rows,seed", [(200, 0), (500, 42), (1000, 7), (1500, 42)])
def test_sizes_schema_and_account_consistency(rows, seed):
    dataset = generate_dataset(GenerationConfig(rows=rows, seed=seed))
    assert len(dataset.feedback) == rows
    assert validate_feedback(dataset.feedback).valid
    assert set(dataset.feedback.columns) == set(REQUIRED + OPTIONAL)
    assert dataset.feedback.feedback_id.is_unique
    assert dataset.labels.feedback_id.is_unique
    assert set(dataset.feedback.feedback_id) == set(dataset.labels.feedback_id)
    signals = dataset.feedback.groupby("customer_id")[["segment", "account_value"]].nunique()
    assert (signals == 1).all().all()
    assert dataset.feedback.customer_id.nunique() < rows
    assert set(dataset.feedback.segment) == {"Startup", "SMB", "Enterprise"}
    dates = pd.to_datetime(dataset.feedback.request_date)
    assert dates.between(pd.Timestamp(START_DATE), pd.Timestamp(END_DATE)).all()


def test_reproducibility_and_different_seed(dataset, tmp_path):
    repeat = generate_dataset(dataset.config)
    pd.testing.assert_frame_equal(dataset.feedback, repeat.feedback)
    pd.testing.assert_frame_equal(dataset.labels, repeat.labels)
    pd.testing.assert_frame_equal(dataset.customers, repeat.customers)
    first, second = tmp_path / "first", tmp_path / "second"
    write_dataset(dataset, first)
    write_dataset(repeat, second)
    files = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
    assert len(files) == 8
    for path in files:
        assert (first / path).read_bytes() == (second / path).read_bytes()
    different = generate_dataset(GenerationConfig(seed=43))
    assert not different.feedback.equals(dataset.feedback)


def test_split_isolation_and_model_input_allowlist(dataset):
    tuning = dataset.labels[dataset.labels.split == "tuning"]
    evaluation = dataset.labels[dataset.labels.split == "evaluation"]
    for column in ("feedback_id", "template_family", "duplicate_group"):
        assert not (set(tuning[column]) - {""}) & (set(evaluation[column]) - {""})
    tune_input, eval_input = dataset.feedback_for("tuning"), dataset.feedback_for("evaluation")
    assert set(tune_input.customer_id).isdisjoint(eval_input.customer_id)
    normalise = lambda values: {" ".join(text.lower().split()) for text in values}
    assert normalise(tune_input.feedback_text).isdisjoint(normalise(eval_input.feedback_text))
    for split in ("tuning", "evaluation"):
        frame = dataset.model_input(split)
        assert list(frame.columns) == ["feedback_id", "feedback_text"]
        assert len(frame) >= 200
        assert set(frame.feedback_id) == set(dataset.labels.loc[dataset.labels.split == split, "feedback_id"])
    assert set(tuning.loc[tuning.eligible_single_theme, "primary_theme"]) == set(
        evaluation.loc[evaluation.eligible_single_theme, "primary_theme"])


def test_annotations_and_paraphrases(dataset):
    joined = dataset.feedback.merge(dataset.labels, on="feedback_id", validate="one_to_one")
    clear = joined[joined.label_kind == "clear"]
    challenge = joined[joined.label_kind != "clear"]
    assert len(clear) == 425
    assert len(joined[joined.label_kind == "overlapping"]) == 50
    assert len(joined[joined.label_kind == "ambiguous"]) == 25
    assert clear.eligible_single_theme.all() and clear.eligible_duplicate.all()
    assert not challenge.eligible_single_theme.any() and not challenge.eligible_duplicate.any()
    assert challenge.duplicate_group.eq("").all()
    assert challenge.primary_theme.eq("").all()
    assert challenge.effort.isna().all()
    assert joined.loc[joined.label_kind == "ambiguous", "theme_labels"].eq("").all()
    assert joined.loc[joined.label_kind == "overlapping", "theme_labels"].str.split("|").map(len).eq(2).all()
    # Each clear intent has multiple wordings; related intents retain separate labels.
    assert clear.groupby("duplicate_group").feedback_text.nunique().ge(3).all()
    assert clear.groupby("primary_theme").duplicate_group.nunique().eq(4).all()
    assert clear.groupby("duplicate_group").effort.nunique().eq(1).all()


def test_business_conflicts_and_emerging_trend(dataset):
    joined = dataset.feedback.merge(dataset.labels, on="feedback_id")
    cosmetic = joined[joined.primary_theme == "dashboard_customisation"]
    enterprise = joined[joined.primary_theme.isin(["audit_history", "identity_access"])]
    assert len(cosmetic) > len(enterprise)
    assert cosmetic.customer_id.nunique() <= 6
    assert cosmetic.segment.eq("Startup").all()
    assert enterprise.segment.eq("Enterprise").all()
    assert enterprise.account_value.min() > cosmetic.account_value.max()
    assert enterprise.strategic_alignment.min() > cosmetic.strategic_alignment.max()
    assert enterprise.urgency.min() > cosmetic.urgency.max()
    assert cosmetic.votes.sum() > enterprise.votes.sum()
    usage = joined[joined.primary_theme == "usage_alerts"]
    recent = pd.to_datetime(usage.request_date) > pd.Timestamp(END_DATE) - pd.Timedelta(days=30)
    assert recent.mean() >= 0.70
    assert not recent.all()


def test_written_bundle_hashes_roundtrip_and_no_truth_in_inputs(dataset, tmp_path):
    output = tmp_path / "dataset"
    manifest = write_dataset(dataset, output)
    assert manifest == json.loads((output / "manifest.json").read_text())
    for filename, digest in manifest["files_sha256"].items():
        content = (output / filename).read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest
        if filename.startswith("inputs/"):
            frame = read_feedback(content, filename)
            assert validate_feedback(frame).valid
            assert set(frame.columns) == set(REQUIRED + OPTIONAL)
        if filename.startswith("model_inputs/"):
            assert (output / filename).read_text().splitlines()[0] == "feedback_id,feedback_text"
    original = (output / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        write_dataset(dataset, output)
    assert (output / "manifest.json").read_bytes() == original


@pytest.mark.parametrize("kwargs", [
    {"rows": 0}, {"rows": 199}, {"rows": 10_001}, {"rows": 500.5},
    {"rows": True}, {"seed": -1}, {"seed": 2**32}, {"seed": "42"},
])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        GenerationConfig(**kwargs)


def test_unknown_split_rejected(dataset):
    with pytest.raises(ValueError, match="split"):
        dataset.model_input("test")


def test_integrity_catches_account_corruption():
    dataset = generate_dataset()
    dataset.feedback.loc[0, "account_value"] = 1
    with pytest.raises(ValueError, match="registry"):
        assert_integrity(dataset)


def test_integrity_catches_label_join_corruption():
    dataset = generate_dataset()
    dataset.labels.loc[0, "feedback_id"] = "missing"
    with pytest.raises(ValueError, match="one-to-one"):
        assert_integrity(dataset)


def test_integrity_catches_incorrect_truth_annotation():
    dataset = generate_dataset()
    ambiguous_index = dataset.labels.index[dataset.labels.label_kind == "ambiguous"][0]
    dataset.labels.loc[ambiguous_index, "eligible_single_theme"] = True
    with pytest.raises(ValueError, match="Truth annotation"):
        assert_integrity(dataset)


def test_catalog_has_distinct_phrasings_and_balanced_families():
    assert len({family.key for family in FAMILIES}) == len(FAMILIES)
    phrases = [phrase.casefold().strip() for family in FAMILIES for phrase in family.phrases]
    assert len(set(phrases)) == len(phrases)
    assert len(FAMILIES) == 32
    assert all(len(family.phrases) == 3 for family in FAMILIES)


def test_cli_creates_bundle_and_refuses_overwrite(tmp_path):
    output = tmp_path / "cli-dataset"
    command = [sys.executable, "-m", "productlens.synthetic", "--rows", "500", "--seed", "42", "--output", str(output)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["rows"] == 500
    assert (output / "manifest.json").is_file()
    retry = subprocess.run(command, capture_output=True, text=True)
    assert retry.returncode == 2
    assert "Generation failed" in retry.stderr
    assert "Traceback" not in retry.stderr
