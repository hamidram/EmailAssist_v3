from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

REQUIRED_COLUMNS = frozenset({"date_received", "sender", "subject", "body"})
DATE_FORMATS = ("%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y")


def load_emails(path: Path) -> list[dict[str, str]]:
    """Load email rows from CSV and normalize their received dates to ISO format."""
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            rows = _read_rows(csv_file)
    except UnicodeDecodeError:
        with path.open("r", encoding="latin-1", newline="") as csv_file:
            rows = _read_rows(csv_file)

    return rows


def _read_rows(csv_file) -> list[dict[str, str]]:
    reader = csv.DictReader(csv_file)
    if reader.fieldnames is None:
        raise ValueError("The input CSV is empty or missing a header row.")

    missing_columns = REQUIRED_COLUMNS.difference(reader.fieldnames)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"The input CSV is missing required columns: {missing}.")

    rows: list[dict[str, str]] = []
    for row_number, source_row in enumerate(reader, start=2):
        if None in source_row:
            raise ValueError(f"CSV row {row_number} has more values than its header.")
        row = {key: value or "" for key, value in source_row.items() if key is not None}
        try:
            row["date_received"] = parse_received_date(row["date_received"]).isoformat()
        except ValueError as exc:
            raise ValueError(
                f"Invalid date_received in CSV row {row_number}: "
                f"{row['date_received']!r}."
            ) from exc
        if not row.get("email_id"):
            row["email_id"] = str(row_number - 1)
        rows.append(row)
    return rows


def parse_received_date(value: str) -> date:
    normalized = value.strip()
    if not normalized:
        raise ValueError("A received date cannot be blank.")
    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value!r}.")


def filter_yesterbox(emails: list[dict[str, str]], as_of: date) -> list[dict[str, str]]:
    yesterday = as_of - timedelta(days=1)
    return [
        email
        for email in emails
        if parse_received_date(email["date_received"]) == yesterday
    ]
