"""Streamlit view of evidence-linked candidate groups."""

import hashlib
import json
from pathlib import Path

import streamlit as st

from productlens.embeddings import EmbeddingUnavailable, MODEL_ID, MODEL_REVISION
from productlens.grouping import GroupingConfig, MAX_GROUPING_ROWS, group_feedback

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "semantic.json"


def render_semantic_groups(data):
    st.header("Explore related requests")
    st.write("Group similar feedback into candidate opportunities, then inspect the evidence before deciding what to build.")
    if not CONFIG_PATH.is_file():
        st.info("Semantic grouping settings are not configured yet.")
        return
    try:
        saved = json.loads(CONFIG_PATH.read_text())
        if (saved["model_id"], saved["model_revision"]) != (MODEL_ID, MODEL_REVISION):
            raise ValueError("The configured model differs from the installed model.")
        config = GroupingConfig(**saved["grouping"])
    except (ValueError, KeyError) as exc:
        st.error(f"Could not load grouping settings: {exc}")
        return
    signature = hashlib.sha256(data.to_csv(index=False).encode() + CONFIG_PATH.read_bytes()).hexdigest()
    cached = st.session_state.get("semantic_result")
    if cached is not None and cached[0] != signature:
        st.session_state.pop("semantic_result", None)
    too_large = len(data) > MAX_GROUPING_ROWS
    if too_large:
        st.warning(f"Upload at most {MAX_GROUPING_ROWS:,} rows to run semantic grouping.")
    if st.button("Group related feedback", disabled=too_large):
        st.session_state.pop("semantic_result", None)
        try:
            with st.spinner("Analysing feedback locally. The first run may download the semantic model."):
                result = group_feedback(data, config)
            st.session_state.semantic_result = (signature, result)
        except (EmbeddingUnavailable, ValueError) as exc:
            st.error(str(exc))
    st.caption("AI suggestions need review. Each request has one group, so overlapping needs may be missed. Prioritisation is the next milestone.")
    with st.expander("How these groups are formed"):
        st.write(f"Model: {MODEL_ID}; revision: {MODEL_REVISION}. Feedback text is embedded locally on CPU.")
        st.write(f"Complete-linkage cosine thresholds: opportunities {config.opportunity_similarity:.2f}; "
                 f"candidate duplicates {config.duplicate_similarity:.2f}. Settings were selected on synthetic tuning data.")
        st.write("Titles use phrases from the feedback and a representative source request. Similarity is not a confidence probability. "
                 "Groups are shown by evidence volume; no priority score has been calculated.")
    cached = st.session_state.get("semantic_result")
    if cached is None or cached[0] != signature:
        return
    result = cached[1]
    st.success(f"Semantic grouping complete: {len(result.opportunities)} candidate opportunities.")
    if result.assignments.text_truncated.any():
        st.warning(f"{int(result.assignments.text_truncated.sum())} request(s) exceeded the model's 256-token window. "
                   "Only the beginning was embedded; review the full original text below.")
    opportunities = result.opportunities.sort_values(["request_count", "opportunity_id"], ascending=[False, True])
    st.dataframe(opportunities[["opportunity_id", "key_terms", "request_count", "distinct_customers",
                                "unique_wordings", "duplicate_groups", "review_note"]], hide_index=True, width="stretch")
    descriptions = opportunities.set_index("opportunity_id").key_terms.to_dict()
    selected = st.selectbox("Inspect an opportunity", opportunities.opportunity_id.tolist(),
                            format_func=lambda identifier: f"{identifier}: {descriptions[identifier]}", key="opportunity_picker")
    opportunity = opportunities[opportunities.opportunity_id == selected].iloc[0]
    st.write("**Representative source request:**", opportunity.representative_request)
    st.caption(f"Source: {opportunity.representative_feedback_id}. {opportunity.review_note}")
    evidence = data.merge(result.assignments, on="feedback_id", validate="one_to_one")
    evidence = evidence[evidence.opportunity_id == selected]
    st.subheader("Supporting feedback")
    st.dataframe(evidence, hide_index=True, width="stretch")
    st.subheader("Candidate duplicate groups within this opportunity")
    st.caption("These stricter groups help separate specific requests inside a broad opportunity. "
               "Examples are original feedback; review each group before treating it as one feature.")
    duplicate_summary = evidence.groupby("duplicate_group_id", sort=True).agg(
        example_request=("feedback_text", "first"), request_count=("feedback_id", "size"),
        distinct_customers=("customer_id", "nunique"),
    ).reset_index()
    st.dataframe(duplicate_summary, hide_index=True, width="stretch")
