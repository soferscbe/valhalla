import json
from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from productlens.embeddings import EmbeddingUnavailable, MODEL_ID, MODEL_REVISION
from productlens.grouping import group_feedback

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def configured_ui(monkeypatch, tmp_path):
    config = tmp_path / "semantic.json"
    config.write_text(json.dumps({"model_id": MODEL_ID, "model_revision": MODEL_REVISION,
                                  "grouping": {"opportunity_similarity": .7, "duplicate_similarity": .9}}))
    monkeypatch.setattr("productlens.ui_semantics.CONFIG_PATH", config)
    # Deliberately controlled test vectors, not claimed real-model performance.
    def controlled(data, config):
        return group_feedback(data, config, lambda texts: (np.eye(len(texts)), [False] * len(texts)))
    monkeypatch.setattr("productlens.ui_semantics.group_feedback", controlled)


def start_sample():
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio[0].set_value("Try synthetic sample").run()
    return app


def test_grouping_review_persists_across_selection_and_clears_on_source_change(configured_ui):
    app = start_sample()
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert any("Semantic grouping complete" in item.value for item in app.success)
    assert len(app.dataframe) == 4
    assert len(app.selectbox[0].options) == 6
    # Changing selection reruns the UI without recomputing or losing groups.
    app.selectbox[0].select_index(1).run()
    assert not app.exception
    assert len(app.dataframe) == 4
    assert "feedback_id" in app.dataframe[2].value.columns
    assert app.dataframe[3].value.request_count.sum() == len(app.dataframe[2].value)
    app.radio[0].set_value("Upload a file").run()
    assert not app.dataframe
    assert "semantic_result" not in app.session_state


def test_grouping_failure_is_visible_without_fallback(configured_ui, monkeypatch):
    def unavailable(*args, **kwargs):
        raise EmbeddingUnavailable("Model unavailable in this test.")
    monkeypatch.setattr("productlens.ui_semantics.group_feedback", unavailable)
    app = start_sample()
    app.button[0].click().run()
    assert not app.exception
    assert any("Model unavailable" in item.value for item in app.error)
    assert not app.selectbox
    assert not any("Semantic grouping complete" in item.value for item in app.success)


def test_new_invalid_upload_removes_prior_groups(configured_ui):
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.file_uploader[0].upload("valid.csv", b"feedback_id,customer_id,feedback_text\n1,c1,Audit history\n2,c2,Audit log").run()
    app.button[0].click().run()
    assert app.selectbox
    app.file_uploader[0].upload("invalid.csv", b"feedback_id,customer_id,feedback_text\n1,c1, ").run()
    assert app.error and not app.selectbox
    assert "semantic_result" not in app.session_state
