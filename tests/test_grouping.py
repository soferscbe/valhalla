import numpy as np
import pandas as pd
import pytest

from productlens.grouping import GroupingConfig, group_feedback, prepare_feedback
from productlens.grouping_metrics import pair_metrics, clustering_metrics


def frame(texts, customers=None):
    return pd.DataFrame({"feedback_id": [f"F{i}" for i in range(len(texts))],
                         "customer_id": customers or [f"C{i}" for i in range(len(texts))],
                         "feedback_text": texts})


def encoder(texts):
    vectors = {"email report": [1, 0, 0], "weekly summary": [0.95, 0.3, 0],
               "audit log": [0, 0, 1], "export activity": [0.1, 0, 0.95]}
    return np.array([vectors[text] for text in texts]), [False] * len(texts)


def test_traceability_counts_and_nested_duplicates():
    data = frame(["Email report", " email   REPORT ", "Weekly summary", "Audit log"], ["C1", "C1", "C2", "C3"])
    result = group_feedback(data, GroupingConfig(.7, .99), encoder)
    assert len(result.opportunities) == 2
    assert set(result.assignments.feedback_id) == set(data.feedback_id)
    assert result.assignments.feedback_id.is_unique
    group = result.opportunities[result.opportunities.request_count == 3].iloc[0]
    assert group.distinct_customers == 2
    assert group.unique_wordings == 2
    assert group.duplicate_groups == 2
    assert group.representative_feedback_id in {"F0", "F2"}
    assert result.assignments.groupby("duplicate_group_id").opportunity_id.nunique().max() == 1
    assert result.assignments.similarity_to_representative.between(-1, 1).all()


def test_permutation_and_volume_do_not_change_unique_wording_groups():
    data = frame(["Email report", "Weekly summary", "Audit log", "Export activity"])
    baseline = group_feedback(data, GroupingConfig(.7, .9), encoder)
    shuffled = group_feedback(data.sample(frac=1, random_state=4), GroupingConfig(.7, .9), encoder)
    pd.testing.assert_frame_equal(baseline.assignments, shuffled.assignments)
    extras = pd.concat([data, frame(["Email report"] * 10).assign(feedback_id=lambda x: "extra" + x.feedback_id)], ignore_index=True)
    expanded = group_feedback(extras, GroupingConfig(.7, .9), encoder)
    assert set(expanded.opportunities.opportunity_id) == set(baseline.opportunities.opportunity_id)


def test_encoder_receives_only_text_and_input_is_unchanged():
    data = frame(["Audit log", "Email report"])
    data["theme_label"] = ["secret label", "another label"]
    data["account_value"] = [99, 100]
    before = data.copy(deep=True)
    seen = []
    def recording(texts):
        seen.extend(texts)
        return encoder(texts)
    group_feedback(data, GroupingConfig(.7, .9), recording)
    assert seen == ["audit log", "email report"]
    pd.testing.assert_frame_equal(before, data)


def test_complete_linkage_prevents_similarity_chain():
    data = frame(["a", "b", "c"])
    angles = np.deg2rad([0, 30, 60])
    vectors = np.column_stack([np.cos(angles), np.sin(angles)])
    result = group_feedback(data, GroupingConfig(.7, .9), lambda texts: (vectors, [False] * 3))
    assert len(result.opportunities) == 2  # Endpoints have cosine 0.5, cannot all merge.


def test_empty_and_singleton():
    def fail_if_called(texts):
        raise AssertionError("Empty data must not call encoder")
    assert group_feedback(frame([]), GroupingConfig(.7, .9), fail_if_called).assignments.empty
    result = group_feedback(frame(["Audit log"]), GroupingConfig(.7, .9), encoder)
    assert len(result.opportunities) == 1
    assert result.opportunities.iloc[0].unique_wordings == 1
    assert result.assignments.iloc[0].similarity_to_representative == pytest.approx(1)


@pytest.mark.parametrize("broad,strict", [(0, .9), (.7, 1), (.9, .7), (float("nan"), .8)])
def test_invalid_thresholds(broad, strict):
    with pytest.raises(ValueError):
        GroupingConfig(broad, strict)


@pytest.mark.parametrize("vectors", [[[0, 0]], [[float("nan"), 1]], [[1, 0], [1, 1]], [1, 2]])
def test_bad_encoder_output(vectors):
    with pytest.raises(ValueError):
        prepare_feedback(frame(["Audit log"]), lambda texts: (vectors, [False]))


def test_truncation_flags_follow_original_rows():
    data = frame(["Audit log", "Audit log", "Email report"])
    result = group_feedback(data, GroupingConfig(.7, .9), lambda texts: (encoder(texts)[0], [True, False]))
    assert result.assignments.text_truncated.tolist() == [True, True, False]


def test_size_limit_and_invalid_input():
    with pytest.raises(ValueError, match="2,000"):
        prepare_feedback(frame(["Audit log"] * 2001), encoder)
    with pytest.raises(ValueError, match="invalid feedback"):
        prepare_feedback(frame([" "]), encoder)


def test_pair_metrics_known_counts_and_undefined_cases():
    result = pair_metrics(["a", "a", "b"], ["x", "x", "x"], ["one", "two", "three"])
    assert result["true_positive"] == 1
    assert result["false_positive"] == 2
    assert result["precision"] == pytest.approx(1/3)
    assert result["recall"] == 1
    assert result["f1"] == .5
    empty = pair_metrics(["a"], ["x"], ["one"])
    assert empty["precision"] is None and empty["f1"] is None
    filtered = pair_metrics(["a", "a", "b"], ["x", "x", "x"], ["one", "one", "two"], True)
    assert filtered["pair_count"] == 2 and filtered["true_positive"] == 0


def test_metric_eligibility_unique_weighting_and_missing_predictions():
    evidence = frame(["Email report", "Email report", "Weekly summary", "vague"])
    evidence["eligible_single_theme"] = evidence["eligible_duplicate"] = [True, True, True, False]
    evidence["primary_theme"] = ["reports", "reports", "reports", ""]
    evidence["duplicate_group"] = ["weekly", "weekly", "weekly", ""]
    assignments = pd.DataFrame({"feedback_id": evidence.feedback_id, "opportunity_id": ["a"] * 4,
                                "duplicate_group_id": ["b"] * 4})
    metrics = clustering_metrics(evidence, assignments)
    assert metrics["eligible_rows"] == 3
    assert metrics["excluded_challenge_rows"] == 1
    assert metrics["unique_texts"]["count"] == 2
    assert metrics["rows"]["theme_ari"] == 1
    assert metrics["rows"]["duplicate_pairs"]["f1"] == 1
    with pytest.raises(ValueError, match="exactly once"):
        clustering_metrics(evidence, assignments.iloc[:2])
