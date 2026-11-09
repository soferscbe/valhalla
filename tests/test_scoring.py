import numpy as np
import pandas as pd
import pytest

from productlens.scoring import (DEFAULT_WEIGHTS, METHODS, aggregate_evidence, compare_scores,
                                 score_opportunities, segment_representation)
from productlens.ui_scoring import export_csv


def fixture():
    data = pd.DataFrame([
        ("1", "a", "request one", "Enterprise", 100, 2, 5, 3, 4),
        ("2", "a", "request one again", "Enterprise", 100, 3, 5, 3, 4),
        ("3", "b", "request two", "SMB", 50, 1, 1, 5, 6),
        ("4", "c", "another need", "SMB", 200, 10, 3, 1, 2),
    ], columns=["feedback_id", "customer_id", "feedback_text", "segment", "account_value", "votes", "urgency", "strategic_alignment", "effort"])
    links = pd.DataFrame([("1", "A", "x"), ("2", "A", "x"), ("3", "A", "y"), ("4", "B", "z")],
                         columns=["feedback_id", "opportunity_id", "duplicate_group_id"])
    return data, links


def test_customer_aggregation_and_hand_calculated_scores():
    data, links = fixture()
    evidence = aggregate_evidence(data, links)
    rows = evidence.opportunities.set_index("opportunity_id")
    assert rows.loc["A", ["request_count", "distinct_customers", "arr", "votes", "effort_proxy"]].tolist() == [3, 2, 150, 6, 10]
    assert rows.loc["A", "urgency"] == 3  # equal customers, not mean of three records
    assert rows.loc["A", "alignment"] == 4
    result = score_opportunities(evidence)
    a = result.scores.set_index("opportunity_id").loc["A"]
    assert a.benefit == pytest.approx(30 + 22.5 + 10 + 15)
    assert a.priority_score == pytest.approx(7.75)
    assert a.rice_score == pytest.approx(.06)
    assert a.weighted_score == pytest.approx(77.5)
    assert result.normalisation == {"reach": 2., "arr": 200.}
    assert result.scores.opportunity_id.tolist() == ["B", "A"]  # B: (15+30+10)/2 =27.5
    assert set(evidence.rows.feedback_id) == set(data.feedback_id)


def test_repetition_changes_votes_and_volume_but_not_other_scores():
    data, links = fixture()
    before = score_opportunities(aggregate_evidence(data, links)).scores.set_index("opportunity_id")
    repeated = pd.concat([data, data.iloc[[0]].assign(feedback_id="5")], ignore_index=True)
    repeated_links = pd.concat([links, links.iloc[[0]].assign(feedback_id="5")], ignore_index=True)
    after = score_opportunities(aggregate_evidence(repeated, repeated_links)).scores.set_index("opportunity_id")
    for field in ("arr", "distinct_customers", "effort_proxy", "urgency", "alignment", "priority_score", "rice_score"):
        pd.testing.assert_series_equal(before[field], after[field])
    assert after.loc["A", "votes_score"] == before.loc["A", "votes_score"] + 2


def test_missing_active_factor_never_becomes_zero_and_zero_weight_can_exclude_it():
    data, links = fixture()
    data.loc[3, "account_value"] = np.nan
    evidence = aggregate_evidence(data, links)
    scores = score_opportunities(evidence).scores.set_index("opportunity_id")
    assert pd.isna(scores.loc["B", "priority_score"])
    assert pd.isna(scores.loc["B", "weighted_score"])
    assert scores.loc["B", "rice_score"] > 0
    assert "arr" in scores.loc["B", "score_status"]
    alternative = score_opportunities(evidence, dict(reach=1, arr=0, urgency=0, alignment=0)).scores.set_index("opportunity_id")
    assert alternative.loc["B", "priority_score"] == 25
    assert alternative.loc["B", "contribution_arr"] == 0


def test_effort_conflicts_and_missing_subgroup_are_visible():
    data, links = fixture()
    data.loc[1, "effort"] = 8
    data.loc[2, "effort"] = np.nan
    evidence = aggregate_evidence(data, links)
    assert evidence.subgroups.set_index("duplicate_group_id").loc["x", "effort_proxy"] == 8
    a = score_opportunities(evidence).scores.set_index("opportunity_id").loc["A"]
    assert pd.isna(a.priority_score) and pd.isna(a.rice_score)
    assert a.weighted_score > 0 and a.votes_score == 6
    assert "Conflicting effort" in a.warnings
    assert "effort" in a.score_status


def test_global_account_conflict_affects_every_opportunity_for_that_account():
    data, links = fixture()
    data.loc[3, "customer_id"] = "a"
    evidence = aggregate_evidence(data, links)
    assert evidence.opportunities.arr.isna().all()
    assert evidence.accounts.set_index("customer_id").loc["a", "account_value_status"] == "conflicting"
    assert evidence.accounts.set_index("customer_id").loc["a", "segment"] == "Unknown/conflicting"
    assert evidence.opportunities.set_index("opportunity_id").loc["A", "known_arr"] == 50


def test_partial_known_assessments_and_global_arr_resolution_are_flagged():
    data, links = fixture()
    data.loc[0, ["account_value", "urgency", "effort"]] = np.nan
    data.loc[0, "strategic_alignment"] = 5
    evidence = aggregate_evidence(data, links)
    a = evidence.opportunities.set_index("opportunity_id").loc["A"]
    assert a.arr == 150 and a.effort_proxy == 10 and a.urgency == 3
    assert a.alignment == 4.5
    assert "conflicting assessments" in a.warnings
    assert "missing observations" in a.warnings


def test_only_required_input_retained_unranked_and_empty_supported():
    data, links = fixture()
    data = data[["feedback_id", "customer_id", "feedback_text"]]
    result = score_opportunities(aggregate_evidence(data, links))
    assert len(result.scores) == 2
    assert result.scores[list(METHODS)].isna().all().all()
    empty = aggregate_evidence(data.iloc[:0], links.iloc[:0])
    assert score_opportunities(empty).scores.empty
    assert segment_representation(empty, score_opportunities(empty).scores, "priority_score") == []


@pytest.mark.parametrize("change", ["missing", "extra", "repeated", "blank", "cross_group"])
def test_bad_assignment_contract_rejected(change):
    data, links = fixture()
    if change == "missing": links = links.iloc[1:]
    if change == "extra": links = pd.concat([links, links.iloc[[0]].assign(feedback_id="new")])
    if change == "repeated": links = pd.concat([links, links.iloc[[0]]])
    if change == "blank": links.loc[0, "opportunity_id"] = " "
    if change == "cross_group": links.loc[3, "duplicate_group_id"] = "x"
    with pytest.raises(ValueError): aggregate_evidence(data, links)


@pytest.mark.parametrize("weights", [dict(reach=0, arr=0, urgency=0, alignment=0),
    dict(reach=-1, arr=1, urgency=1, alignment=1), dict(reach=float("nan"), arr=1, urgency=1, alignment=1),
    dict(reach=float("inf"), arr=1, urgency=1, alignment=1), {"reach": 1}])
def test_bad_weights_rejected(weights):
    with pytest.raises(ValueError): score_opportunities(aggregate_evidence(*fixture()), weights)


def test_weights_change_priority_without_changing_baselines():
    evidence = aggregate_evidence(*fixture())
    default = score_opportunities(evidence).scores.set_index("opportunity_id")
    alternative = score_opportunities(evidence, dict(reach=0, arr=0, urgency=0, alignment=1)).scores.set_index("opportunity_id")
    assert alternative.priority_score.idxmax() == "A"
    for method in METHODS[1:]: pd.testing.assert_series_equal(default[method].sort_index(), alternative[method].sort_index())
    doubled = score_opportunities(evidence, {f: v * 2 for f, v in DEFAULT_WEIGHTS.items()}).scores
    pd.testing.assert_frame_equal(score_opportunities(evidence).scores, doubled)


def test_reordering_is_exactly_reproducible():
    data, links = fixture()
    before = aggregate_evidence(data, links)
    after = aggregate_evidence(data.sample(frac=1, random_state=4), links.sample(frac=1, random_state=7))
    for field in ("accounts", "subgroups", "rows", "opportunities"):
        pd.testing.assert_frame_equal(getattr(before, field), getattr(after, field))
    pd.testing.assert_frame_equal(score_opportunities(before).scores, score_opportunities(after).scores)


def test_ties_undefined_correlations_and_common_candidate_denominators():
    scores = pd.DataFrame({"opportunity_id": ["c", "b", "a", "d"], "x": [2., 2., 1., np.nan], "y": [1., 2., 3., 9.]})
    report = compare_scores(scores, "x", "y", k=1)
    assert report["common_candidates"] == 3 and report["comparison_coverage"] == 4
    assert report["spearman"] == pytest.approx(-np.sqrt(3) / 2)
    assert report["top_k_agreement"] == 0
    assert report["rank_changes"][0] == dict(opportunity_id="a", reference_rank=3., comparison_rank=1., rank_change=-2.)
    scores["y"] = 2.
    assert compare_scores(scores, "x", "y")["spearman"] is None
    scores["y"] = np.nan
    assert compare_scores(scores, "x", "y")["top_k_agreement"] is None


def test_segment_coverage_counts_union_of_customers_and_exports_are_safe():
    evidence = aggregate_evidence(*fixture())
    result = score_opportunities(evidence)
    coverage = {r["segment"]: r for r in segment_representation(evidence, result.scores, "priority_score", k=1)}
    assert coverage["Enterprise"]["coverage"] == 0
    assert coverage["SMB"]["selected_customers"] == 1 and coverage["SMB"]["total_customers"] == 2
    csv = export_csv(pd.DataFrame({"text": ["=1+1", " @evil", "ok"], "value": [-2, 1, 3]})).decode()
    assert "'=1+1" in csv and "' @evil" in csv and ",-2" in csv


def test_all_zero_arr_and_confidence_bounds():
    data, links = fixture()
    data["account_value"] = 0
    evidence = aggregate_evidence(data, links)
    assert score_opportunities(evidence).scores.factor_arr.eq(0).all()
    assert score_opportunities(evidence, confidence=0).scores.rice_score.eq(0).all()
    for confidence in (-1, 1.1, float("nan")):
        with pytest.raises(ValueError): score_opportunities(evidence, confidence=confidence)
