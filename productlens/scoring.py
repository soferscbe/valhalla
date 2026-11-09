"""Auditable deterministic scoring; see docs/SCORING_PROTOCOL.md for assumptions."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from productlens.ingestion import OPTIONAL, REQUIRED, validate_feedback

FACTORS = ("reach", "arr", "urgency", "alignment")
DEFAULT_WEIGHTS = dict(zip(FACTORS, (.30, .30, .20, .20)))
METHODS = ("priority_score", "votes_score", "weighted_score", "rice_score")


@dataclass
class Evidence:
    opportunities: pd.DataFrame
    accounts: pd.DataFrame
    subgroups: pd.DataFrame
    rows: pd.DataFrame


@dataclass
class ScoringResult:
    scores: pd.DataFrame
    weights: dict[str, float]
    normalisation: dict[str, float | None]
    confidence: float


def _known(series):
    return sorted(series.dropna().unique().tolist())


def aggregate_evidence(frame: pd.DataFrame, assignments: pd.DataFrame) -> Evidence:
    """Validate identity coverage and keep unresolved signals explicit, never zero-filled."""
    if frame.empty and all(c in frame for c in REQUIRED):
        data = frame.copy()
    else:
        validation = validate_feedback(frame)
        if not validation.valid:
            raise ValueError("Invalid scoring data: " + "; ".join(validation.errors))
        data = validation.data
    required = ["feedback_id", "opportunity_id", "duplicate_group_id"]
    if any(c not in assignments for c in required):
        raise ValueError("Assignments require feedback, opportunity and duplicate group IDs.")
    links = assignments[required].copy()
    if (links.isna().any().any() or links.map(lambda x: not isinstance(x, str) or not x.strip()).any().any()
            or links.feedback_id.duplicated().any()
            or set(links.feedback_id) != set(data.feedback_id)):
        raise ValueError("Assignments must cover exactly every feedback ID once with non-empty string IDs.")
    if (links.groupby("duplicate_group_id").opportunity_id.nunique() > 1).any():
        raise ValueError("A duplicate group cannot span different opportunities.")
    for column in OPTIONAL:
        if column not in data:
            data[column] = pd.NA
    for column in ("account_value", "votes", "urgency", "strategic_alignment", "effort"):
        data[column] = pd.to_numeric(data[column]).astype(float)
    rows = data.merge(links, on="feedback_id", validate="one_to_one").sort_values("feedback_id").reset_index(drop=True)
    account_columns = ["customer_id", "account_value", "account_value_status", "segment", "missing_arr_rows"]
    accounts = []
    for customer, records in data.groupby("customer_id", sort=True):
        values, segments = _known(records.account_value), _known(records.segment)
        accounts.append(dict(customer_id=customer, account_value=values[0] if len(values) == 1 else np.nan,
                             account_value_status="known" if len(values) == 1 else "conflicting" if values else "missing",
                             segment=segments[0] if len(segments) == 1 else "Unknown/conflicting",
                             missing_arr_rows=int(records.account_value.isna().sum())))
    accounts = pd.DataFrame(accounts, columns=account_columns)
    subgroup_columns = ["opportunity_id", "duplicate_group_id", "effort_proxy", "distinct_estimates",
                        "missing_effort_rows", "feedback_ids"]
    subgroups = []
    for (opportunity, duplicate), records in rows.groupby(["opportunity_id", "duplicate_group_id"], sort=True):
        values = _known(records.effort)
        subgroups.append(dict(opportunity_id=opportunity, duplicate_group_id=duplicate,
                              effort_proxy=max(values) if values else np.nan, distinct_estimates=len(values),
                              missing_effort_rows=int(records.effort.isna().sum()),
                              feedback_ids=" | ".join(records.feedback_id)))
    subgroups = pd.DataFrame(subgroups, columns=subgroup_columns)
    opportunity_columns = ["opportunity_id", "request_count", "distinct_customers", "votes", "arr",
                           "known_arr", "arr_coverage", "urgency", "alignment", "effort_proxy",
                           "duplicate_groups", "feedback_ids", "customer_ids", "warnings"]
    opportunities = []
    for opportunity, records in rows.groupby("opportunity_id", sort=True):
        customer_ids = sorted(records.customer_id.unique())
        customer_rows = accounts[accounts.customer_id.isin(customer_ids)]
        groups = subgroups[subgroups.opportunity_id == opportunity]
        warnings = ["Candidate grouping and scope require human review."]
        unknown_arr = customer_rows.account_value.isna().sum()
        if unknown_arr:
            warnings.append(f"ARR unresolved for {unknown_arr} customer(s), including conflicts or missing values.")
        if customer_rows.missing_arr_rows.sum():
            warnings.append("Some account-value observations are missing; use globally resolved values where consistent.")
        if (customer_rows.segment == "Unknown/conflicting").any():
            warnings.append("Some customer segments are missing or conflicting.")
        ratings = {}
        for column, name in (("urgency", "urgency"), ("strategic_alignment", "alignment")):
            estimates = [_known(part[column]) for _, part in records.groupby("customer_id", sort=True)]
            ratings[name] = float(np.mean([np.mean(values) for values in estimates])) if all(estimates) else np.nan
            if records[column].isna().any():
                warnings.append(f"{name}: missing observations; customers with no known assessment make the factor unknown.")
            if any(len(values) > 1 for values in estimates):
                warnings.append(f"{name}: conflicting assessments averaged within customers using distinct values.")
        effort = float(groups.effort_proxy.sum()) if groups.effort_proxy.notna().all() else np.nan
        if groups.missing_effort_rows.sum():
            warnings.append("Missing effort observations; a subgroup with no estimate makes total effort unknown.")
        if (groups.distinct_estimates > 1).any():
            warnings.append("Conflicting effort estimates: maximum per candidate duplicate subgroup used.")
        votes = float(records.votes.sum()) if records.votes.notna().all() else np.nan
        if pd.isna(votes):
            warnings.append("Incomplete votes; vote baseline unavailable.")
        opportunities.append(dict(
            opportunity_id=opportunity, request_count=len(records), distinct_customers=len(customer_ids),
            votes=votes, arr=float(customer_rows.account_value.sum()) if not unknown_arr else np.nan,
            known_arr=float(customer_rows.account_value.sum()), arr_coverage=float(1 - unknown_arr / len(customer_rows)),
            **ratings, effort_proxy=effort, duplicate_groups=len(groups),
            feedback_ids=" | ".join(records.feedback_id), customer_ids=" | ".join(customer_ids), warnings=" ".join(warnings)))
    return Evidence(pd.DataFrame(opportunities, columns=opportunity_columns), accounts, subgroups, rows)


def score_opportunities(evidence: Evidence, weights=None, confidence=.5) -> ScoringResult:
    raw = DEFAULT_WEIGHTS if weights is None else weights
    if set(raw) != set(FACTORS):
        raise ValueError("Provide exactly reach, arr, urgency and alignment weights.")
    vector = np.asarray([raw[name] for name in FACTORS], dtype=float)
    if not np.isfinite(vector).all() or (vector < 0).any() or not np.isfinite(vector.sum()) or vector.sum() <= 0:
        raise ValueError("Weights must be finite, nonnegative and have a positive sum.")
    if not np.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("Common RICE-style confidence must be between zero and one.")
    normalised = dict(zip(FACTORS, (vector / vector.sum()).tolist()))
    scored = evidence.opportunities.copy()
    maxima = {}
    for factor, column in (("reach", "distinct_customers"), ("arr", "arr")):
        values = pd.to_numeric(scored[column]).astype(float)
        maximum = values.max()
        maxima[factor] = float(maximum) if pd.notna(maximum) else None
        scored[f"factor_{factor}"] = values / maximum if pd.notna(maximum) and maximum > 0 else values * 0
    for factor in ("urgency", "alignment"):
        scored[f"factor_{factor}"] = (pd.to_numeric(scored[factor]).astype(float) - 1) / 4
    for factor in FACTORS:
        scored[f"contribution_{factor}"] = (
            100 * normalised[factor] * scored[f"factor_{factor}"] if normalised[factor] else 0.0)
    scored["benefit"] = scored[[f"contribution_{factor}" for factor in FACTORS]].sum(axis=1, min_count=4)
    scored["priority_score"] = scored.benefit / pd.to_numeric(scored.effort_proxy).astype(float)
    scored["weighted_score"] = sum(100 * DEFAULT_WEIGHTS[f] * scored[f"factor_{f}"] for f in FACTORS)
    scored["votes_score"] = pd.to_numeric(scored.votes).astype(float)
    scored["rice_score"] = (pd.to_numeric(scored.distinct_customers).astype(float)
                            * pd.to_numeric(scored.urgency).astype(float) / 5 * confidence
                            / pd.to_numeric(scored.effort_proxy).astype(float))
    reasons = []
    for _, row in scored.iterrows():
        missing = [f for f in FACTORS if normalised[f] and pd.isna(row[f"factor_{f}"])]
        if pd.isna(row.effort_proxy):
            missing.append("effort")
        reasons.append("Missing/unresolved: " + ", ".join(missing) if missing else "Scored provisionally; review grouping and effort.")
    scored["score_status"] = reasons
    for method in METHODS:
        scored[method + "_rank"] = scored[method].rank(ascending=False, method="average")
    return ScoringResult(scored.sort_values(["priority_score", "opportunity_id"], ascending=[False, True],
                                           na_position="last").reset_index(drop=True), normalised, maxima, float(confidence))


def compare_scores(scores: pd.DataFrame, reference: str, comparison: str, k=5) -> dict:
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("K must be a positive integer.")
    common = scores.dropna(subset=[reference, comparison]).copy()
    n = len(common)
    rank_a, rank_b = (common[column].rank(ascending=False, method="average") for column in (reference, comparison))
    correlation = float(rank_a.corr(rank_b)) if n > 1 and rank_a.nunique() > 1 and rank_b.nunique() > 1 else None
    limit = min(k, n)
    tops = [set(common.sort_values([column, "opportunity_id"], ascending=[False, True]).head(limit).opportunity_id)
            for column in (reference, comparison)]
    changes = [{"opportunity_id": row.opportunity_id, "reference_rank": float(rank_a.loc[index]),
                "comparison_rank": float(rank_b.loc[index]), "rank_change": float(rank_b.loc[index] - rank_a.loc[index])}
               for index, row in common.sort_values("opportunity_id").iterrows()]
    return dict(reference=reference, comparison=comparison, total_candidates=len(scores),
                reference_coverage=int(scores[reference].notna().sum()), comparison_coverage=int(scores[comparison].notna().sum()),
                common_candidates=n, k=limit, spearman=correlation,
                top_k_agreement=len(tops[0] & tops[1]) / limit if limit else None, rank_changes=changes)


def segment_representation(evidence: Evidence, scores: pd.DataFrame, method: str, k=5) -> list[dict]:
    top = scores.dropna(subset=[method]).sort_values([method, "opportunity_id"], ascending=[False, True]).head(k)
    selected = set(evidence.rows[evidence.rows.opportunity_id.isin(top.opportunity_id)].customer_id)
    return [dict(segment=segment, selected_customers=int(accounts.customer_id.isin(selected).sum()),
                 total_customers=len(accounts), coverage=float(accounts.customer_id.isin(selected).mean()))
            for segment, accounts in evidence.accounts.groupby("segment", sort=True)]
