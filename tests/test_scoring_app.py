from pathlib import Path

import numpy as np
from streamlit.testing.v1 import AppTest

from productlens.grouping import group_feedback

APP = Path(__file__).resolve().parents[1] / "app.py"


def start(monkeypatch):
    def controlled(data, config):
        return group_feedback(data, config, lambda texts: (np.eye(len(texts)), [False] * len(texts)))
    monkeypatch.setattr("productlens.ui_semantics.group_feedback", controlled)
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio[0].set_value("Try synthetic sample").run()
    app.button[0].click().run()
    return app


def score_table(app):
    return next(item.value for item in app.dataframe if "priority_score" in item.value.columns).set_index("opportunity_id")


def test_weights_rerank_live_without_recomputing_groups(monkeypatch):
    app = start(monkeypatch)
    assert not app.exception and not app.error
    before = score_table(app)
    cached = app.session_state.semantic_result[1].assignments.copy()
    app.slider(key="weight_arr").set_value(100).run()
    assert not app.exception and not app.error
    after = score_table(app)
    assert not before.priority_score.sort_index().equals(after.priority_score.sort_index())
    assert cached.equals(app.session_state.semantic_result[1].assignments)
    app.selectbox(key="score_picker").select_index(1).run()
    assert not app.exception
    assert len(score_table(app)) == len(before)


def test_zero_weights_and_source_changes_clear_prior_rankings(monkeypatch):
    app = start(monkeypatch)
    for factor in ("reach", "arr", "urgency", "alignment"):
        app.slider(key=f"weight_{factor}").set_value(0)
    app.run()
    assert not app.exception
    assert any("at least one strategy weight" in item.value for item in app.info)
    assert not any("priority_score" in item.value.columns for item in app.dataframe)
    app.radio[0].set_value("Upload a file").run()
    assert not app.dataframe


def test_missing_business_signals_keep_candidates_visible(monkeypatch):
    app = start(monkeypatch)
    app.radio[0].set_value("Upload a file").run()
    app.file_uploader[0].upload("minimal.csv", b"feedback_id,customer_id,feedback_text\n1,a,Audit logs\n2,b,More reports").run()
    app.button[0].click().run()
    assert not app.exception and not app.error
    scores = score_table(app)
    assert len(scores) == 2 and scores.priority_score.isna().all()
    assert any("0 of 2" in item.value for item in app.success)
