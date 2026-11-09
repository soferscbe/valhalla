from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def start_app():
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()


def test_empty_start_and_synthetic_sample():
    app = start_app()
    assert not app.exception
    assert not app.success
    app.radio[0].set_value("Try synthetic sample").run()
    assert not app.exception
    assert app.success
    assert [metric.value for metric in app.metric] == ["6", "5", "1"]
    assert len(app.dataframe[0].value) == 6


@pytest.mark.parametrize("extension", ["csv", "xlsx"])
def test_real_upload_widget_valid_files(extension):
    content = (ROOT / "data/sample_feedback.csv").read_bytes()
    if extension == "xlsx":
        buffer = BytesIO()
        pd.read_csv(BytesIO(content)).to_excel(buffer, index=False)
        content = buffer.getvalue()
    app = start_app()
    app.file_uploader[0].upload("feedback." + extension, content).run()
    assert not app.exception
    assert app.success
    assert [metric.value for metric in app.metric] == ["6", "5", "1"]


def test_invalid_upload_clears_previous_valid_preview():
    app = start_app()
    app.file_uploader[0].upload("valid.csv", (ROOT / "data/sample_feedback.csv").read_bytes()).run()
    assert app.success
    app.file_uploader[0].upload("invalid.csv", b"feedback_id,customer_id,feedback_text\nF1,C1, ").run()
    assert not app.exception
    assert app.error
    assert not app.success
    assert not app.metric
    assert any("feedback_text must not be blank" in error.value for error in app.error)
    app.file_uploader[0].clear().run()
    assert not app.success
    assert not app.dataframe


def test_malformed_upload_shows_error_without_traceback():
    app = start_app()
    app.file_uploader[0].upload("broken.xlsx", b"broken").run()
    assert not app.exception
    assert "Could not read" in app.error[0].value


def test_generated_dataset_file_loads_in_app(tmp_path):
    from productlens.synthetic import generate_dataset, write_dataset

    dataset = generate_dataset()
    output = tmp_path / "generated"
    write_dataset(dataset, output)
    app = start_app()
    app.file_uploader[0].upload("synthetic_feedback.csv", (output / "inputs/feedback.csv").read_bytes()).run()
    assert not app.exception
    assert not app.error
    assert app.success
    assert app.metric[0].value == "500"
    assert app.metric[1].value == str(dataset.feedback.customer_id.nunique())
    assert len(app.dataframe[0].value) == 500
    assert "theme_labels" not in app.dataframe[0].value.columns
    assert app.warning  # Missing effort on ambiguous/multi-intent requests is explicit.
