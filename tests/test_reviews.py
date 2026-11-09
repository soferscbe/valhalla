from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from productlens.grouping import GroupingConfig, group_feedback
from productlens.reviews import ReviewError, ReviewStore, canonical, make_snapshot, new_workspace_key, workspace_digest
from productlens.scoring import DEFAULT_WEIGHTS, aggregate_evidence, score_opportunities


def context(weights=None, data=None):
    if data is None:
        data = pd.read_csv(Path(__file__).resolve().parents[1] / "data/sample_feedback.csv", dtype=str)
    groups = group_feedback(data, GroupingConfig(.7,.9), lambda texts: (np.eye(len(texts)), [False] * len(texts)))
    evidence = aggregate_evidence(data, groups.assignments)
    scores = score_opportunities(evidence, weights)
    return make_snapshot(evidence, groups, scores, {"grouping": {"opportunity_similarity": .7, "duplicate_similarity": .9}})


def test_history_persists_across_new_process_and_key_is_not_stored(tmp_path):
    store = ReviewStore(sqlite_path=tmp_path / "reviews.sqlite3")
    key = new_workspace_key()
    identifier, snapshot = context()
    opportunity = snapshot["scores"][0]["opportunity_id"]
    saved = store.save(key, identifier, snapshot, opportunity, "Accept", "Synthetic demonstration, reviewed scope", "Test reviewer")
    # A separate interpreter, not an in-memory object, must retrieve this exact event.
    script = "import json,sys; from productlens.reviews import ReviewStore; print(json.dumps(ReviewStore(sqlite_path=sys.argv[1]).history(sys.stdin.read())))"
    result = subprocess.run([sys.executable, "-c", script, str(store.path)], input=key, capture_output=True, text=True, check=True)
    history = json.loads(result.stdout)
    assert len(history) == 1 and history[0]["event_id"] == saved
    assert "+00:00" in history[0]["created_at"]
    assert key.encode() not in store.path.read_bytes()
    exported = store.export(key)
    assert key not in json.dumps(exported)
    assert exported["snapshots"][identifier] == snapshot
    assert "workspace" not in exported["events"][0]
    assert store.path.stat().st_mode & 0o777 == 0o600


def test_workspace_isolation_and_append_only_history(tmp_path):
    store = ReviewStore(sqlite_path=tmp_path / "reviews.sqlite3")
    key, other = new_workspace_key(), new_workspace_key()
    identifier, snapshot = context()
    opportunity = snapshot["scores"][0]["opportunity_id"]
    first = store.save(key, identifier, snapshot, opportunity, "Defer", "Need an estimate")
    second = store.save(key, identifier, snapshot, opportunity, "Override priority", "Strategic commitment", manual_priority="High")
    history = store.history(key)
    assert [event["event_id"] for event in history] == [second, first]
    assert history[0]["manual_priority"] == "High" and history[1]["manual_priority"] is None
    assert store.history(other) == [] and store.export(other)["snapshots"] == {}
    assert len(store.export(key)["snapshots"]) == 1


def test_context_changes_for_data_and_strategy_but_not_row_order():
    original_id, snapshot = context()
    data = pd.read_csv(Path(__file__).resolve().parents[1] / "data/sample_feedback.csv", dtype=str)
    shuffled_id, shuffled = context(data=data.sample(frac=1, random_state=11))
    assert original_id == shuffled_id and snapshot == shuffled
    weights = DEFAULT_WEIGHTS | {"arr": .9}
    assert context(weights=weights)[0] != original_id
    data.loc[0, "votes"] = "9"
    assert context(data=data)[0] != original_id


@pytest.mark.parametrize("change", ["blank_reason", "long_reason", "bad_action", "bad_override", "unexpected_priority", "unknown_opportunity", "tampered_snapshot", "bad_key"])
def test_invalid_save_never_records_an_event(tmp_path, change):
    store = ReviewStore(sqlite_path=tmp_path / "reviews.sqlite3")
    key = new_workspace_key()
    identifier, snapshot = context()
    values = dict(key=key, context_id=identifier, snapshot=snapshot, opportunity_id=snapshot["scores"][0]["opportunity_id"], action="Accept", reason="Reviewed")
    if change == "blank_reason": values["reason"] = "  "
    if change == "long_reason": values["reason"] = "x" * 4001
    if change == "bad_action": values["action"] = "Unrecognised"
    if change == "bad_override": values["action"] = "Override priority"
    if change == "unexpected_priority": values["manual_priority"] = "High"
    if change == "unknown_opportunity": values["opportunity_id"] = "not-in-data"
    if change == "tampered_snapshot": snapshot["weights"]["arr"] = 999
    if change == "bad_key": values["key"] = "guessable"
    with pytest.raises(ReviewError): store.save(**values)
    assert store.history(key) == []
    assert store.export(key)["snapshots"] == {}


def test_failed_event_insert_rolls_back_snapshot(tmp_path):
    store = ReviewStore(sqlite_path=tmp_path / "reviews.sqlite3")
    key = new_workspace_key()
    store.history(key)  # initialise schema
    with sqlite3.connect(store.path) as connection:
        connection.execute("CREATE TRIGGER reject_review BEFORE INSERT ON productlens_review_events BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    identifier, snapshot = context()
    with pytest.raises(ReviewError, match="no save was confirmed"):
        store.save(key, identifier, snapshot, snapshot["scores"][0]["opportunity_id"], "Accept", "Test failure")
    assert store.export(key) == dict(format="productlens-review-export-v1", events=[], snapshots={})


def test_concurrent_append_retains_all_events(tmp_path):
    store = ReviewStore(sqlite_path=tmp_path / "reviews.sqlite3")
    key = new_workspace_key()
    store.history(key)
    identifier, snapshot = context()
    def append(index):
        return store.save(key, identifier, snapshot, snapshot["scores"][0]["opportunity_id"], "Defer", f"Review {index}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(append, range(8)))
    assert len(set(ids)) == 8 and len(store.history(key)) == 8


def test_cloud_never_falls_back_and_errors_do_not_expose_credentials(tmp_path):
    with pytest.raises(ReviewError, match="fallback is disabled"):
        ReviewStore.from_settings({"PRODUCTLENS_DEPLOYMENT": "cloud"})
    with pytest.raises(ReviewError, match="sslmode"):
        ReviewStore.from_settings({"PRODUCTLENS_DEPLOYMENT": "cloud", "PRODUCTLENS_DATABASE_URL": "postgresql://private:secret@example.test/db"})
    store = ReviewStore.from_settings({"PRODUCTLENS_DEPLOYMENT": "cloud", "PRODUCTLENS_DATABASE_URL": "postgresql://private:secret@example.test/db?sslmode=require"})
    assert store.path is None and "secret" not in store.description
    # An existing directory cannot be used as a SQLite database.
    with pytest.raises(ReviewError) as caught:
        ReviewStore(sqlite_path=tmp_path).history(new_workspace_key())
    assert str(tmp_path) not in str(caught.value)
    assert "unavailable" in str(caught.value)


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("PRODUCTLENS_TEST_POSTGRES_URL"), reason="Requires an explicitly supplied test PostgreSQL database")
def test_real_postgres_round_trip():
    store = ReviewStore(postgres_url=os.environ["PRODUCTLENS_TEST_POSTGRES_URL"])
    key = new_workspace_key()
    identifier, snapshot = context()
    event = store.save(key, identifier, snapshot, snapshot["scores"][0]["opportunity_id"], "Defer", "Automated synthetic PostgreSQL integration check")
    assert ReviewStore(postgres_url=os.environ["PRODUCTLENS_TEST_POSTGRES_URL"]).history(key)[0]["event_id"] == event
    assert store.export(key)["snapshots"][identifier] == snapshot
    assert store.history(new_workspace_key()) == []
