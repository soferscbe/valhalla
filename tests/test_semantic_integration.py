"""Opt-in tests with the pinned, locally cached real model; never mock embeddings."""

import os
from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from productlens.embeddings import encode_texts

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("PRODUCTLENS_TEST_REAL_MODEL") != "1", reason="Opt in with PRODUCTLENS_TEST_REAL_MODEL=1 after downloading model")]


def test_real_embeddings_are_repeatable_and_text_sensitive():
    texts = ["Email a weekly usage report", "Send the usage summary every week", "Enforce two factor login"]
    first, flags = encode_texts(texts)
    second, _ = encode_texts(texts)
    assert first.shape == (3, 384)
    assert flags == [False] * 3
    np.testing.assert_allclose(first, second, atol=1e-6)
    assert first[0] @ first[1] > first[0] @ first[2]
    _, truncation = encode_texts(["report " * 400])
    assert truncation == [True]


def test_generated_upload_to_real_semantic_groups(tmp_path, monkeypatch):
    from productlens.synthetic import generate_dataset

    monkeypatch.setenv("PRODUCTLENS_REVIEW_DB", str(tmp_path / "real-model-reviews.sqlite3"))
    monkeypatch.setenv("PRODUCTLENS_DEPLOYMENT", "local")
    data = generate_dataset().feedback
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=120).run()
    app.file_uploader[0].upload("synthetic.csv", data.to_csv(index=False).encode()).run()
    app.button[0].click().run(timeout=120)
    assert not app.exception and not app.error
    assert any("Semantic grouping complete" in item.value for item in app.success)
    cached = app.session_state.semantic_result[1]
    assert len(cached.assignments) == 500
    assert cached.opportunities.request_count.sum() == 500
    assert set(cached.assignments.feedback_id) == set(data.feedback_id)
    assert app.selectbox

    assert any("Scoring complete" in item.value for item in app.success)
    score_table = next(item.value for item in app.dataframe if "priority_score" in item.value.columns)
    assert len(score_table) == len(cached.opportunities)
    assert score_table.request_count.sum() == 500
    assert score_table.priority_score.notna().any()

    next(button for button in app.button if button.label == "Start a new review workspace").click().run()
    app.text_area[0].set_value("Automated synthetic journey: inspect scope before any roadmap commitment.")
    next(button for button in app.button if button.label == "Save review").click().run()
    assert not app.exception and not app.error
    assert any("Review saved" in item.value for item in app.success)
    from productlens.reviews import ReviewStore
    exported = ReviewStore(sqlite_path=tmp_path / "real-model-reviews.sqlite3").export(app.session_state.review_workspace_key)
    assert len(exported["events"]) == 1
    snapshot = next(iter(exported["snapshots"].values()))
    assert len(snapshot["rows"]) == 500
    assert {row["feedback_id"] for row in snapshot["rows"]} == set(data.feedback_id)
