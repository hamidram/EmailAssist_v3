from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from .config import Settings
from .llm_client import OpenAIClient
from .parser import filter_yesterbox, load_emails
from .pipeline import EmailAssistPipeline
from .safety import SafeBrowsingChecker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Triage yesterday's email, summarize critical items, and draft replies."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/Alex_emails_march_04.csv"),
        help="Input CSV file (default: data/Alex_emails_march_04.csv).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for the processed CSV and Markdown report.",
    )
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=date.today(),
        metavar="YYYY-MM-DD",
        help="Treat the previous calendar day as yesterday (default: today).",
    )
    parser.add_argument(
        "--all-emails",
        action="store_true",
        help="Process every row instead of filtering to the day before --as-of.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_environment()
    emails = load_emails(args.input)
    selected_emails = (
        emails if args.all_emails else filter_yesterbox(emails, args.as_of)
    )
    pipeline = EmailAssistPipeline(
        OpenAIClient(settings),
        SafeBrowsingChecker(
            settings.safe_browsing_api_key, timeout=settings.safe_browsing_timeout
        ),
        input_cost_per_million=settings.input_cost_per_million,
        output_cost_per_million=settings.output_cost_per_million,
    )
    processed, report = pipeline.run(
        selected_emails, as_of=args.as_of.isoformat()
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "processed_emails.csv"
    report_path = args.output_dir / "email_assist_report.md"
    _write_csv(csv_path, emails, processed)
    report_path.write_text(report, encoding="utf-8")

    print(f"Processed {len(processed)} email(s).")
    print(f"CSV: {csv_path}")
    print(f"Report: {report_path}")
    return 0


def _write_csv(
    path: Path, source_emails: list[dict[str, str]], processed: list[dict[str, Any]]
) -> None:
    original_columns = list(source_emails[0]) if source_emails else ["email_id"]
    result_columns = [
        key
        for email in processed
        for key in email
        if key not in original_columns
    ]
    fieldnames = original_columns + list(dict.fromkeys(result_columns))
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in processed:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
            )


if __name__ == "__main__":
    raise SystemExit(main())
