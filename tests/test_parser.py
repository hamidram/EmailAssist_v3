from datetime import date

import pytest

from email_assist.parser import filter_yesterbox, load_emails, parse_received_date


def test_load_emails_normalizes_dates_and_filters_yesterdaybox(tmp_path):
    csv_path = tmp_path / "emails.csv"
    csv_path.write_text(
        "email_id,date_received,sender,subject,body\n"
        "a,3/3/2025,Alice,Yesterday,Please review.\n"
        "b,3/4/2025,Bob,Today,For your information.\n",
        encoding="utf-8",
    )

    emails = load_emails(csv_path)

    assert emails[0]["date_received"] == "2025-03-03"
    assert [email["email_id"] for email in filter_yesterbox(emails, date(2025, 3, 4))] == [
        "a"
    ]


def test_load_emails_rejects_missing_required_columns(tmp_path):
    csv_path = tmp_path / "emails.csv"
    csv_path.write_text("date_received,sender\n3/3/2025,Alice\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_emails(csv_path)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("3/3/2025", date(2025, 3, 3)), ("2025-03-03", date(2025, 3, 3))],
)
def test_parse_received_date(value, expected):
    assert parse_received_date(value) == expected
