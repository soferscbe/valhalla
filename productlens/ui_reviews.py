"""Explicit, isolated human decisions over immutable evidence/strategy snapshots."""

import json
import os

import pandas as pd
import streamlit as st

from productlens.reviews import ACTIONS, PRIORITIES, ReviewError, ReviewStore, make_snapshot, new_workspace_key, workspace_digest


def render_reviews(evidence, groups, scoring, semantic_config, selected):
    st.header("Record a human review")
    candidate = groups.opportunities.set_index("opportunity_id").loc[selected]
    st.write(f"**Reviewing:** {candidate.key_terms} ({selected})")
    st.write("Accept, defer or assign a manual priority with a reason. The calculated scores stay unchanged.")
    st.caption("Saving stores a copy of this dataset, its evidence and scoring assumptions in the review backend. "
               "Use only synthetic/nonconfidential data. Reviewer labels are self-reported.")
    settings = {name: os.environ[name] for name in ("PRODUCTLENS_DEPLOYMENT", "PRODUCTLENS_DATABASE_URL", "PRODUCTLENS_REVIEW_DB") if name in os.environ}
    try:
        for name in ("PRODUCTLENS_DEPLOYMENT", "PRODUCTLENS_DATABASE_URL", "PRODUCTLENS_REVIEW_DB"):
            if name not in settings and name in st.secrets:
                settings[name] = st.secrets[name]
    except st.errors.StreamlitSecretNotFoundError:
        pass
    try:
        store = ReviewStore.from_settings(settings)
    except ReviewError as exc:
        st.error(str(exc))
        return
    st.caption("Review storage: " + store.description)
    with st.expander("Private review workspace and recovery"):
        st.write("Start a workspace, then keep its recovery key somewhere private. Reopen it after a browser refresh "
                 "using that key. Anyone with the key can read and add reviews; this is a demo access mechanism, not a verified account.")
        if st.button("Start a new review workspace", key="new_review_workspace"):
            st.session_state.review_workspace_key = new_workspace_key()
        recovery = st.text_input("Existing recovery key", type="password", key="restore_review_key")
        if st.button("Open existing workspace", key="open_review_workspace"):
            try:
                workspace_digest(recovery)
                st.session_state.review_workspace_key = recovery
            except ReviewError as exc:
                st.error(str(exc))
        if "review_workspace_key" in st.session_state:
            st.text_input("Current workspace recovery key — keep private", value=st.session_state.review_workspace_key,
                          type="password", key="display_review_key_" + workspace_digest(st.session_state.review_workspace_key)[:12], disabled=True)
            st.download_button("Download private recovery key", st.session_state.review_workspace_key,
                               "productlens-review-key.txt", "text/plain")
    key = st.session_state.get("review_workspace_key")
    if not key:
        st.info("Open or start a private review workspace above to record decisions.")
        return
    context_id, snapshot = make_snapshot(evidence, groups, scoring, semantic_config)
    st.caption("Current evidence and strategy version: " + context_id[:12])
    # Context-specific widget keys prevent an old draft from being attached to changed inputs/weights.
    scope = workspace_digest(key)[:12] + context_id + selected
    action = st.selectbox("Review action", ACTIONS, key="review_action_" + scope)
    priority = st.selectbox("Manual priority", PRIORITIES, key="review_priority_" + scope) if action == "Override priority" else None
    with st.form("review_form_" + scope, clear_on_submit=False):
        reviewer = st.text_input("Reviewer label (optional)", max_chars=100, key="reviewer_" + scope)
        reason = st.text_area("Reason for this decision", max_chars=4000, key="review_reason_" + scope)
        submitted = st.form_submit_button("Save review")
    if submitted:
        try:
            event_id = store.save(key, context_id, snapshot, selected, action, reason, reviewer, priority)
            st.success("Review saved. Event " + event_id[:8] + ".")
        except ReviewError as exc:
            st.error(str(exc))
    try:
        history = store.history(key)
    except ReviewError as exc:
        st.error(str(exc))
        return
    current = [event for event in history if event["context_id"] == context_id]
    latest = {}
    for event in current:
        latest.setdefault(event["opportunity_id"], event)
    st.subheader("Decisions for this evidence and strategy")
    if latest:
        st.dataframe(pd.DataFrame(latest.values())[["opportunity_id", "action", "manual_priority", "reason", "reviewer", "created_at"]],
                     hide_index=True, width="stretch")
    else:
        st.info("No saved decisions apply to this exact evidence and strategy yet.")
    historical = len(history) - len(current)
    st.caption(f"{len(current)} event(s) in this context; {historical} event(s) belong to other evidence/strategy versions and are not applied here.")
    with st.expander("Append-only review history and export"):
        if history:
            st.dataframe(pd.DataFrame(history), hide_index=True, width="stretch")
            try:
                st.download_button("Download review history and evidence", json.dumps(store.export(key), indent=2, ensure_ascii=False),
                                   "productlens_reviews.json", "application/json")
            except ReviewError as exc:
                st.error(str(exc))
        else:
            st.write("No saved reviews in this workspace.")
