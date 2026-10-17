from __future__ import annotations

import json
from collections import Counter
from typing import Any

from .constants import CATEGORIES, CRITICAL_CATEGORIES
from .llm_client import LLMClient


def build_executive_prompt(emails: list[dict[str, Any]]) -> str:
    counts = Counter(str(email.get("category", "Unknown")) for email in emails)
    ambiguous = []
    for email in emails:
        probabilities = sorted(
            (
                (float(email.get(f"final_{category}_probability", 0.0) or 0.0), category)
                for category in CATEGORIES
            ),
            reverse=True,
        )
        if len(probabilities) > 1 and probabilities[0][0] - probabilities[1][0] <= 0.1:
            ambiguous.append(
                {
                    "email_id": email.get("email_id"),
                    "top_categories": [category for _, category in probabilities[:2]],
                }
            )
    average_body_length = {
        category: round(
            sum(
                int(email.get("email_body_length", 0) or 0)
                for email in emails
                if email.get("category") == category
            )
            / counts[category],
            1,
        )
        for category in CATEGORIES
        if counts[category]
    }
    categorization_cost = sum(
        float(email.get("cost_initial_categorization", 0.0) or 0.0)
        + float(email.get("cost_final_categorization", 0.0) or 0.0)
        for email in emails
    )

    summaries = [
        {
            "email_id": email.get("email_id"),
            "date_received": email.get("date_received"),
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "category": email.get("category"),
            "reason": email.get("reason"),
            "body_length": int(email.get("email_body_length", 0) or 0),
        }
        for email in emails
    ]
    return (
        "Write an executive dashboard for the emails below. Include total reviewed, "
        "category counts, critical items, ambiguity observations, average email "
        "body length by category, categorization cost, and a concise actionable "
        "recommendation. Discuss costs only as estimates. Do not infer missing facts.\n\n"
        f"Category counts: {json.dumps({category: counts[category] for category in CATEGORIES})}\n"
        f"Average body length by category: {json.dumps(average_body_length)}\n"
        f"Ambiguous classifications (top probabilities within 0.1): {json.dumps(ambiguous)}\n"
        f"Estimated categorization cost: ${categorization_cost:.6f}\n"
        f"Emails: {json.dumps(summaries, ensure_ascii=False)}"
    )


def build_report(
    emails: list[dict[str, Any]],
    dashboard: str,
    *,
    as_of: str,
) -> str:
    lines = [
        f"# EmailAssist report — {as_of}",
        "",
        "## Executive dashboard",
        "",
        dashboard,
        "",
        "## Critical emails",
        "",
    ]
    critical_emails = [
        email for email in emails if email.get("category") in CRITICAL_CATEGORIES
    ]
    if not critical_emails:
        lines.append("No urgent or deadline-driven emails were identified.")

    for email in critical_emails:
        lines.extend(
            [
                f"### {email.get('subject') or '(No subject)'}",
                "",
                f"- Email ID: {email.get('email_id', '')}",
                f"- Received: {email.get('date_received', '')}",
                f"- Sender: {email.get('sender', '')}",
                f"- Category: {email.get('category', '')}",
                f"- Summary: {email.get('summary', '')}",
                f"- Next step: {email.get('next_action', '')}",
                "",
                "#### Draft reply",
                "",
                str(email.get("draft_response", "")),
                "",
                "#### Draft evaluation",
                "",
                "```json",
                json.dumps(email.get("evaluation", {}), ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )

    if emails:
        total_cost = sum(float(email.get("total_cost", 0.0) or 0.0) for email in emails)
        total_tokens = round(
            sum(float(email.get("total_tokens", 0) or 0) for email in emails)
        )
    else:
        total_cost = 0.0
        total_tokens = 0
    lines.extend(
        [
            "## LLM usage",
            "",
            f"- Total tokens: {total_tokens}",
            f"- Estimated total cost: ${total_cost:.6f}",
            "",
        ]
    )
    return "\n".join(lines)
