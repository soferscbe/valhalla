"""Strategy controls, baseline comparison and auditable score explanations."""

import json

import pandas as pd
import streamlit as st

from productlens.ui_reviews import render_reviews

from productlens.scoring import (DEFAULT_WEIGHTS, FACTORS, METHODS, aggregate_evidence,
                                 compare_scores, score_opportunities, segment_representation)

LABELS = {"priority_score": "Strategy / effort", "votes_score": "Votes",
          "weighted_score": "Fixed weighted benefit", "rice_score": "RICE-style proxy"}


def export_csv(frame):
    """Protect text cells from spreadsheet formula interpretation in downloaded CSVs."""
    def safe(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    return frame.map(safe).to_csv(index=False).encode("utf-8")


def render_scoring(data, groups, semantic_config):
    st.header("Prioritise with evidence")
    st.write("Explore how business assumptions change the order. Scores are deterministic; AI proposes the groups.")
    st.warning("Provisional priorities: review grouping and effort before a roadmap commitment. "
               "Repeated accounts count once per opportunity. Missing active inputs leave candidates unranked.")
    with st.expander("Strategy weights and assumptions", expanded=True):
        columns = st.columns(4)
        names = {"reach": "Customer reach", "arr": "Account value", "urgency": "Urgency", "alignment": "Strategic alignment"}
        weights = {factor: columns[index].slider(names[factor], 0, 100, int(DEFAULT_WEIGHTS[factor] * 100),
                                                key=f"weight_{factor}") for index, factor in enumerate(FACTORS)}
        confidence = st.slider("Common RICE-style confidence assumption", 0.0, 1.0, .5, .05, key="rice_confidence")
        st.caption("Weights are normalised by their total. Baseline weights stay fixed. Confidence is a common scenario "
                   "assumption, not an AI probability; changing it scales RICE-style scores equally.")
    if not sum(weights.values()):
        st.info("Set at least one strategy weight above zero to calculate priorities.")
        return
    try:
        evidence = aggregate_evidence(data, groups.assignments)
        result = score_opportunities(evidence, weights, confidence)
    except ValueError as exc:
        st.error(f"Cannot calculate priorities: {exc}")
        return
    scores = result.scores.merge(groups.opportunities[["opportunity_id", "key_terms"]], on="opportunity_id", validate="one_to_one")
    ready = int(scores.priority_score.notna().sum())
    st.success(f"Scoring complete: {ready} of {len(scores)} candidates have the inputs needed for this strategy.")
    st.caption("Priority = weighted benefit / provisional effort. Effort is the sum of maximum known estimates "
               "within candidate duplicate groups, not a sum across feedback records. Synthetic units: USD ARR and person-days. "
               "Use consistent units for other uploads. Unknown scores are not zero priorities.")
    st.dataframe(scores[["opportunity_id", "key_terms", "priority_score_rank", "priority_score", "distinct_customers",
                         "request_count", "arr", "effort_proxy", "score_status"]], hide_index=True, width="stretch")
    st.download_button("Download scores and contributions", export_csv(scores), "productlens_scores.csv", "text/csv")
    st.download_button("Download scoring assumptions", json.dumps(dict(protocol="scoring-v1", weights=result.weights,
        normalisation=result.normalisation, common_confidence=result.confidence), indent=2),
        "productlens_scoring_assumptions.json", "application/json")
    chosen = st.selectbox("Explain a priority", scores.opportunity_id.tolist(), key="score_picker")
    row = scores.set_index("opportunity_id").loc[chosen]
    factors = pd.DataFrame([dict(factor=f, normalised_signal=row[f"factor_{f}"], weight=result.weights[f],
                                 benefit_contribution=row[f"contribution_{f}"]) for f in FACTORS])
    st.subheader("Why this score?")
    st.write(f"**{row.key_terms}** — {row.score_status}")
    st.dataframe(factors, hide_index=True, width="stretch")
    def display(value):
        return "not available" if pd.isna(value) else f"{value:.3f}"
    st.write(f"Benefit: {display(row.benefit)}; effort proxy: {display(row.effort_proxy)}; priority: {display(row.priority_score)}.")
    st.caption(row.warnings)
    with st.expander("Inspect the calculation inputs and source feedback"):
        st.write("Normalisation maxima for this uploaded candidate set:", result.normalisation)
        st.write("Reach and ARR divide by their respective maxima; urgency and alignment use (assessment − 1) / 4. "
                 "Every positive-weight factor must be known. Exact score ties share average rank; ID breaks display/Top-K ties only.")
        source = evidence.rows[evidence.rows.opportunity_id == chosen]
        st.write("Resolved accounts (once per customer; conflicts remain unknown)")
        st.dataframe(evidence.accounts[evidence.accounts.customer_id.isin(source.customer_id)], hide_index=True, width="stretch")
        st.write("Provisional effort by candidate duplicate subgroup")
        st.dataframe(evidence.subgroups[evidence.subgroups.opportunity_id == chosen], hide_index=True, width="stretch")
        st.write("Original supporting records")
        st.dataframe(source, hide_index=True, width="stretch")
    with st.expander("Compare prioritisation methods", expanded=True):
        st.caption("Comparisons describe disagreement, not which method is correct. Votes are record endorsements, "
                   "not unique voters. Fixed weighted benefit omits effort. RICE-style proxy = submitting customers × "
                   "(urgency / 5) × common confidence / effort; this is not forecast reach or validated impact.")
        st.dataframe(scores[["opportunity_id"] + [c for method in METHODS for c in (method, method + "_rank")]],
                     hide_index=True, width="stretch")
        comparisons = [compare_scores(scores, "priority_score", method) for method in METHODS[1:]]
        st.dataframe(pd.DataFrame([{k: v for k, v in comparison.items() if k != "rank_changes"}
                                   for comparison in comparisons]), hide_index=True, width="stretch")
        st.caption("Agreement uses only candidates scored by both methods, with ranks recomputed on that intersection. "
                   "Top-K uses up to five shared candidates; constant ranks have undefined correlation.")
        st.write("Customer segment coverage for the strategy's Top-5")
        st.dataframe(pd.DataFrame(segment_representation(evidence, scores, "priority_score")), hide_index=True, width="stretch")
    render_reviews(evidence, groups, result, semantic_config, chosen)
