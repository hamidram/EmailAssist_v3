from email_assist.charts import write_category_probability_chart
from email_assist.constants import CATEGORIES


def test_category_probability_chart_creates_png(tmp_path):
    emails = [
        {
            f"final_{category}_probability": 0.9 if index == 0 else 0.02
            for index, category in enumerate(CATEGORIES)
        },
        {
            f"final_{category}_probability": 0.5
            for category in CATEGORIES
        },
    ]
    chart_path = tmp_path / "probabilities.png"

    write_category_probability_chart(emails, chart_path)

    assert chart_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_category_probability_chart_handles_no_matching_emails(tmp_path):
    chart_path = tmp_path / "empty.png"

    write_category_probability_chart([], chart_path)

    assert chart_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
