"""Parse and validate feedback without scoring, inferring labels or dropping rows."""

import csv
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

REQUIRED = ("feedback_id", "customer_id", "feedback_text")
OPTIONAL = (
    "segment", "request_date", "account_value", "votes", "urgency",
    "strategic_alignment", "effort",
)
MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 10_000


class FeedbackInputError(ValueError):
    """A user-correctable file error."""


@dataclass
class ValidationResult:
    data: pd.DataFrame
    errors: list[str]
    warnings: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def read_feedback(content: bytes, filename: str) -> pd.DataFrame:
    """Read UTF-8 CSV or the first XLSX worksheet, preserving text identifiers."""
    if not content:
        raise FeedbackInputError("The file is empty. Upload a file with headers and feedback rows.")
    if len(content) > MAX_BYTES:
        raise FeedbackInputError("The file exceeds the 10 MiB upload limit.")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise FeedbackInputError("Use a UTF-8 .csv or .xlsx file. Convert legacy .xls files first.")
    try:
        if suffix == ".csv":
            reader = csv.reader(StringIO(content.decode("utf-8-sig")), strict=True)
            return _read_rows(reader)
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        try:
            return _read_rows(workbook.worksheets[0].iter_rows(values_only=True))
        finally:
            workbook.close()
    except FeedbackInputError:
        raise
    except UnicodeDecodeError as exc:
        raise FeedbackInputError("CSV must use UTF-8 encoding. Save as CSV UTF-8 and try again.") from exc
    except Exception as exc:
        raise FeedbackInputError("Could not read the file. Check its format and re-save it as CSV or XLSX.") from exc


def _read_rows(rows) -> pd.DataFrame:
    iterator = iter(rows)
    headers = next(iterator, None)
    if not headers:
        raise FeedbackInputError("The file has no header row.")
    names = [str(value).strip() if value is not None else "" for value in headers]
    if any(not name for name in names):
        raise FeedbackInputError("Every column needs a non-empty header.")
    if len(set(names)) != len(names):
        raise FeedbackInputError("Column headers must be unique after trimming whitespace.")
    records = []
    for row_number, values in enumerate(iterator, start=2):
        if len(records) >= MAX_ROWS:
            raise FeedbackInputError(f"Use at most {MAX_ROWS:,} feedback rows per file.")
        if len(values) != len(names):
            raise FeedbackInputError(f"Row {row_number} has {len(values)} fields; expected {len(names)}.")
        records.append(values)
    return pd.DataFrame(records, columns=names)


def validate_feedback(frame: pd.DataFrame) -> ValidationResult:
    """Return cleaned known columns plus errors; callers must gate on ``valid``.

    Row numbers refer to spreadsheet rows, with the header at row 1. No rows are
    discarded. Optional blanks remain missing and are reported without imputation.
    """
    errors: list[str] = []
    warnings: list[str] = []
    data = frame.copy(deep=True).reset_index(drop=True)
    data.columns = [str(column).strip() for column in data.columns]
    if data.columns.duplicated().any():
        return ValidationResult(data, ["Column headers must be unique."], warnings)
    missing = [column for column in REQUIRED if column not in data]
    if missing:
        errors.append("Missing required columns: " + ", ".join(missing) + ".")
    if data.empty:
        errors.append("No feedback rows found. Add at least one feedback record.")
    if len(data) > MAX_ROWS:
        errors.append(f"Use at most {MAX_ROWS:,} feedback rows.")
    extra = [column for column in data if column not in REQUIRED + OPTIONAL]
    if extra:
        warnings.append("Excluded unknown columns: " + ", ".join(extra) + ".")
    data = data[[column for column in REQUIRED + OPTIONAL if column in data]].copy()
    if missing or data.empty or len(data) > MAX_ROWS:
        return ValidationResult(data, errors, warnings)

    def flag(mask: pd.Series, message: str) -> None:
        row_numbers = (data.index[mask.fillna(False)] + 2).tolist()
        if row_numbers:
            shown = ", ".join(map(str, row_numbers[:10]))
            suffix = f" (and {len(row_numbers) - 10} more)" if len(row_numbers) > 10 else ""
            errors.append(f"{message} Rows: {shown}{suffix}.")

    for column in data:
        # Native Excel dates are supported; CSV dates must be explicit ISO dates.
        if column == "request_date":
            data[column] = data[column].map(
                lambda value: value.date().isoformat() if isinstance(value, datetime)
                else value.isoformat() if isinstance(value, date) else value
            )
        data[column] = data[column].astype("string").str.strip().replace("", pd.NA)
    for column in REQUIRED:
        flag(data[column].isna(), f"{column} must not be blank.")
    flag(data.feedback_id.notna() & data.feedback_id.duplicated(keep=False),
         "feedback_id must be unique; check duplicated records.")

    for column in OPTIONAL:
        if column not in data:
            continue
        absent = int(data[column].isna().sum())
        if absent:
            warnings.append(f"{column}: {absent} missing value(s); no values were imputed.")
    if "request_date" in data:
        raw = data.request_date
        parsed = pd.to_datetime(raw, format="%Y-%m-%d", errors="coerce")
        flag(raw.notna() & (~raw.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False) | parsed.isna()),
             "request_date must be a valid YYYY-MM-DD date.")
        data["request_date"] = parsed
    for column in ("account_value", "votes", "urgency", "strategic_alignment", "effort"):
        if column not in data:
            continue
        raw = data[column]
        numbers = pd.to_numeric(raw, errors="coerce").astype("Float64")
        invalid = raw.notna() & (numbers.isna() | ~np.isfinite(numbers))
        message = f"{column} must be a finite number"
        if column in {"account_value", "votes"}:
            invalid |= numbers < 0
            message += " greater than or equal to 0"
        elif column == "effort":
            invalid |= numbers <= 0
            message += " greater than 0"
        else:
            invalid |= (numbers < 1) | (numbers > 5)
            message += " between 1 and 5"
        if column == "votes":
            invalid |= numbers.mod(1) != 0
            message += " and a whole number"
        flag(invalid, message + ".")
        data[column] = numbers
    return ValidationResult(data, errors, warnings)
