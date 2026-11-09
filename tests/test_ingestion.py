from datetime import datetime
from io import BytesIO

import pandas as pd
import pytest

from productlens.ingestion import FeedbackInputError, read_feedback, validate_feedback


@pytest.fixture
def feedback():
    return pd.DataFrame({
        "feedback_id": ["001", "002"], "customer_id": ["001", "001"],
        "feedback_text": [" Schedule reports ", "Email weekly usage"],
    })


def test_cleaning_preserves_ids_repeated_customers_and_source(feedback):
    original = feedback.copy(deep=True)
    result = validate_feedback(feedback)
    assert result.valid
    assert result.data.customer_id.nunique() == 1
    assert len(result.data) == 2
    assert result.data.feedback_id.tolist() == ["001", "002"]
    assert result.data.feedback_text.iloc[0] == "Schedule reports"
    pd.testing.assert_frame_equal(original, feedback)


@pytest.mark.parametrize("column,value", [
    ("feedback_id", ""), ("customer_id", None), ("feedback_text", "  "),
    ("account_value", "-1"), ("account_value", "inf"), ("votes", "1.5"),
    ("votes", "-1"), ("urgency", "6"), ("strategic_alignment", "0"),
    ("effort", "0"), ("effort", "nan"), ("effort", "lots"),
    ("request_date", "2026-02-30"), ("request_date", "11/05/2026"),
    ("request_date", "2026-1-1"),
])
def test_invalid_values_report_column_and_row(feedback, column, value):
    feedback[column] = [value, value]
    result = validate_feedback(feedback)
    assert not result.valid
    assert any(column in error and "Rows: 2, 3" in error for error in result.errors)


def test_duplicate_feedback_ids_after_trimming(feedback):
    feedback.feedback_id = ["001", " 001 "]
    assert any("must be unique" in error for error in validate_feedback(feedback).errors)


def test_missing_columns_and_empty_dataset(feedback):
    assert not validate_feedback(feedback.drop(columns="customer_id")).valid
    assert not validate_feedback(feedback.iloc[:0]).valid


def test_optional_missing_values_and_excluded_labels(feedback):
    feedback["effort"] = ["3", ""]
    feedback["theme_label"] = ["reports", "reports"]
    result = validate_feedback(feedback)
    assert result.valid
    assert pd.isna(result.data.effort.iloc[1])
    assert "theme_label" not in result.data
    assert len(result.warnings) == 2


def test_optional_valid_boundaries(feedback):
    feedback["account_value"] = [0, 24000]
    feedback["votes"] = [0, 2]
    feedback["urgency"] = [1, 5]
    feedback["strategic_alignment"] = [5, 1]
    feedback["effort"] = [0.5, 8]
    feedback["request_date"] = ["2024-02-29", "2026-11-05"]
    assert validate_feedback(feedback).valid


@pytest.mark.parametrize("extension", ["csv", "xlsx"])
def test_file_roundtrip_preserves_text_ids(feedback, extension):
    if extension == "csv":
        content = feedback.to_csv(index=False).encode("utf-8-sig")
    else:
        buffer = BytesIO()
        feedback.to_excel(buffer, index=False)
        content = buffer.getvalue()
    frame = read_feedback(content, "feedback." + extension)
    assert frame.feedback_id.iloc[0] == "001"
    assert validate_feedback(frame).valid


def test_excel_native_dates(feedback):
    feedback["request_date"] = [datetime(2026, 11, 1), datetime(2026, 11, 2)]
    buffer = BytesIO()
    feedback.to_excel(buffer, index=False)
    result = validate_feedback(read_feedback(buffer.getvalue(), "feedback.xlsx"))
    assert result.valid
    assert result.data.request_date.iloc[0] == pd.Timestamp("2026-11-01")


@pytest.mark.parametrize("content,name,message", [
    (b"", "empty.csv", "empty"), (b"a,b\n1,2,3", "bad.csv", "Row 2"),
    (b"a,a\n1,2", "bad.csv", "unique"), (b"a, a \n1,2", "bad.csv", "unique"),
    (b",b\n1,2", "bad.csv", "header"), (b"\xff", "bad.csv", "UTF-8"),
    (b"not a workbook", "bad.xlsx", "Could not read"),
    (b"a,b", "old.xls", ".xlsx"), (b'a,b\n"unclosed,2', "bad.csv", "Could not read"),
])
def test_unreadable_files_fail_helpfully(content, name, message):
    with pytest.raises(FeedbackInputError, match=message):
        read_feedback(content, name)


def test_literal_na_is_not_silently_lost():
    frame = read_feedback(b"feedback_id,customer_id,feedback_text\nNA,NA,NA", "na.csv")
    assert validate_feedback(frame).valid
    assert frame.iloc[0].tolist() == ["NA", "NA", "NA"]


def test_upload_limits(monkeypatch):
    monkeypatch.setattr("productlens.ingestion.MAX_BYTES", 5)
    with pytest.raises(FeedbackInputError, match="limit"):
        read_feedback(b"a,b\n1,2", "large.csv")
    monkeypatch.setattr("productlens.ingestion.MAX_BYTES", 100)
    monkeypatch.setattr("productlens.ingestion.MAX_ROWS", 1)
    with pytest.raises(FeedbackInputError, match="at most"):
        read_feedback(b"a,b\n1,2\n3,4", "many.csv")
