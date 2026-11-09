from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from productlens.grouping import group_feedback
from productlens.reviews import ReviewStore

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def configured(monkeypatch, tmp_path):
    db = tmp_path / "reviews.sqlite3"
    monkeypatch.setenv("PRODUCTLENS_REVIEW_DB", str(db))
    monkeypatch.delenv("PRODUCTLENS_DATABASE_URL", raising=False)
    monkeypatch.setenv("PRODUCTLENS_DEPLOYMENT", "local")
    monkeypatch.setattr("productlens.ui_semantics.group_feedback", lambda data, config:
        group_feedback(data, config, lambda texts: (np.eye(len(texts)), [False] * len(texts))))
    return db


def start():
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio[0].set_value("Try synthetic sample").run()
    next(button for button in app.button if button.label == "Group related feedback").click().run()
    return app


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_save_restore_override_and_context_staleness(configured):
    app = start()
    button(app, "Start a new review workspace").click().run()
    assert not app.exception and not app.error
    key = app.session_state.review_workspace_key
    button(app, "Save review").click().run()
    assert any("Provide a reason" in item.value for item in app.error)
    app.text_area[0].set_value("Synthetic demo: scope inspected; proceed to engineering estimation.")
    button(app, "Save review").click().run()
    assert not app.exception and not app.error
    assert any("Review saved" in item.value for item in app.success)
    store = ReviewStore(sqlite_path=configured)
    assert len(store.history(key)) == 1
    app.run()
    assert len(store.history(key)) == 1  # no duplicate save on rerun
    app.slider(key="weight_arr").set_value(90).run()
    assert any("No saved decisions apply" in item.value for item in app.info)
    assert any("1 event(s) belong to other" in item.value for item in app.caption)
    assert app.text_area[0].value == ""  # prior draft not attached to new strategy
    # Fresh browser session cannot see the old workspace until explicitly restored.
    restored = start()
    assert "review_workspace_key" not in restored.session_state
    restored.text_input(key="restore_review_key").set_value(key)
    button(restored, "Open existing workspace").click().run()
    assert not restored.exception
    assert any("1 event(s) in this context" in item.value for item in restored.caption)
    next(item for item in restored.selectbox if item.label == "Review action").set_value("Override priority").run()
    next(item for item in restored.selectbox if item.label == "Manual priority").set_value("High")
    restored.text_area[0].set_value("Synthetic demo: explicit strategic exception.")
    button(restored, "Save review").click().run()
    assert not restored.exception and not restored.error
    assert store.history(key)[0]["manual_priority"] == "High"
    assert len(store.history(key)) == 2


def test_storage_failure_is_visible_without_false_success(configured, monkeypatch):
    app = start()
    button(app, "Start a new review workspace").click().run()
    app.text_area[0].set_value("Test review")
    monkeypatch.setenv("PRODUCTLENS_REVIEW_DB", str(configured.parent))
    button(app, "Save review").click().run()
    assert not app.exception
    assert any("Review storage is unavailable" in item.value for item in app.error)
    assert not any("Review saved" in item.value for item in app.success)


def test_cloud_mode_missing_database_keeps_scores_available(configured, monkeypatch):
    monkeypatch.setenv("PRODUCTLENS_DEPLOYMENT", "cloud")
    app = start()
    assert not app.exception
    assert any("Local-file fallback is disabled" in item.value for item in app.error)
    assert any("Scoring complete" in item.value for item in app.success)
    assert not any(button.label == "Save review" for button in app.button)


def test_cloud_entrypoint_runs_same_app_with_storage_guard(configured):
    app = AppTest.from_file(APP.parent / "deployment/streamlit_app.py", default_timeout=20).run()
    app.radio[0].set_value("Try synthetic sample").run()
    button(app, "Group related feedback").click().run()
    assert not app.exception
    assert any("Scoring complete" in item.value for item in app.success)
    assert any("Local-file fallback is disabled" in item.value for item in app.error)
