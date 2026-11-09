"""Run with: python -m streamlit run app.py."""

from pathlib import Path

import streamlit as st

from productlens.ingestion import FeedbackInputError, read_feedback, validate_feedback
from productlens.ui_semantics import render_semantic_groups

SAMPLE = Path(__file__).parent / "data" / "sample_feedback.csv"

st.set_page_config(page_title="ProductLens AI", page_icon="🔎", layout="wide")
st.title("ProductLens AI")
st.caption("From Customer Voice to Evidence-Based Roadmap Decisions.")
st.header("Upload and validate feedback")
st.write("Start with synthetic feedback. Check the data before using it to inform product priorities.")
st.info("Upload and validate feedback, then explore AI-assisted groups with their source evidence. Prioritisation is not implemented yet.")

with st.expander("File format and validation rules"):
    st.markdown(
        "**Required:** `feedback_id`, `customer_id`, `feedback_text`. Use unique feedback IDs; "
        "the same customer may submit several requests. Store Excel identifiers as text to preserve leading zeros.\n\n"
        "**Optional:** `segment`, `request_date` (YYYY-MM-DD), `account_value` (≥ 0), "
        "`votes` (whole number ≥ 0), `urgency` and `strategic_alignment` (1–5), `effort` (> 0). "
        "Use one currency and effort unit per dataset. Blank optional signals remain missing.\n\n"
        "UTF-8 CSV or XLSX, up to 10 MiB and 10,000 rows. XLSX uses the first worksheet. "
        "Unknown columns are excluded. No rows are automatically removed."
    )
st.download_button("Download synthetic sample CSV", SAMPLE.read_bytes(),
                   file_name="sample_feedback.csv", mime="text/csv")
source = st.radio("Feedback source", ["Upload a file", "Try synthetic sample"], horizontal=True)
content = None
filename = ""
if source == "Try synthetic sample":
    st.caption("Six hand-written synthetic examples for interface testing; not the research dataset.")
    content, filename = SAMPLE.read_bytes(), SAMPLE.name
else:
    uploaded = st.file_uploader("Choose feedback CSV or XLSX", type=["csv", "xlsx"])
    if uploaded is not None:
        content, filename = uploaded.getvalue(), uploaded.name
st.caption("Uploads are processed in this session and are not saved to disk. Use no confidential customer or company data.")
if content is None:
    st.session_state.pop("semantic_result", None)
    st.write("Upload a file or try the synthetic sample to see validation results.")
    st.stop()
try:
    frame = read_feedback(content, filename)
except FeedbackInputError as exc:
    st.session_state.pop("semantic_result", None)
    st.error(str(exc))
    st.stop()

result = validate_feedback(frame)
for warning in result.warnings:
    st.warning(warning)
if not result.valid:
    st.session_state.pop("semantic_result", None)
    st.error("Validation failed. Correct the issues below and upload again.")
    for error in result.errors:
        st.error(error)
    st.subheader("Uploaded data — needs correction")
    st.dataframe(frame.head(100), hide_index=True, width="stretch")
    st.stop()

st.success("Validation passed. Feedback is ready for preview.")
records, customers, repeat = st.columns(3)
records.metric("Feedback records", len(result.data))
customers.metric("Distinct customers", result.data.customer_id.nunique())
repeat.metric("Records beyond one per customer", len(result.data) - result.data.customer_id.nunique())
st.caption("Record count and distinct-customer count are separate signals. Repeated customers are retained.")
st.subheader("Validated feedback")
st.dataframe(result.data, hide_index=True, width="stretch")
render_semantic_groups(result.data)
