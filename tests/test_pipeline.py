import json

from email_assist.constants import CATEGORIES
from email_assist.llm_client import LLMResponse, parse_json_object
from email_assist.pipeline import EmailAssistPipeline
from email_assist.utils import calculate_cost


class FakeLLM:
    def __init__(self):
        self.calls = []

    def complete(self, system_prompt, user_prompt, *, json_mode=False):
        self.calls.append((system_prompt, user_prompt, json_mode))
        if user_prompt.startswith("Analyze the email"):
            result = {
                "urls_found": ["no-url"],
                "spam_indicators_found": ["no_spam_indicators_found"],
                "initial_categorization": _categories("Urgent & High-Priority Emails"),
            }
            return _json_response(result)
        if user_prompt.startswith("Choose the final category"):
            selected = (
                "Urgent & High-Priority Emails"
                if "Subject: Urgent approval" in user_prompt
                else "Routine Updates & Check-ins"
            )
            return _json_response(
                {"final_categorization": _categories(selected)}
            )
        if user_prompt.startswith("Write an executive dashboard"):
            return LLMResponse("Dashboard summary", prompt_tokens=30, completion_tokens=10)
        if user_prompt.startswith("Summarize this critical email"):
            return _json_response({"summary": "A critical request.", "next_action": "Review today."})
        if user_prompt.startswith("Write a professional first-response"):
            return _json_response({"subject": "Re: Request", "body": "Thank you. I will review it."})
        if user_prompt.startswith("Evaluate the supplied assistant draft"):
            return _json_response({"Relevance": {"score": 5, "justification": "Relevant."}})
        raise AssertionError(f"Unexpected prompt: {user_prompt[:60]}")


class FakeSafetyChecker:
    def check(self, urls):
        return {"status": "no_urls"} if not urls else {"status": "not_configured"}


def _categories(selected):
    return {
        category: {
            "probability": 0.9 if category == selected else 0.02,
            "reason": "Matched test email content.",
        }
        for category in CATEGORIES
    }


def _json_response(value):
    return LLMResponse(json.dumps(value), prompt_tokens=10, completion_tokens=4)


def test_pipeline_runs_triage_reports_drafts_and_usage_accounting():
    llm = FakeLLM()
    progress = []
    pipeline = EmailAssistPipeline(
        llm,
        FakeSafetyChecker(),
        input_cost_per_million=1.0,
        output_cost_per_million=2.0,
        progress_callback=progress.append,
    )
    emails = [
        {
            "email_id": "1",
            "date_received": "2025-03-03",
            "sender": "Alice",
            "subject": "Urgent approval",
            "body": "Please review today. {body} $5",
        },
        {
            "email_id": "2",
            "date_received": "2025-03-03",
            "sender": "Bob",
            "subject": "Weekly update",
            "body": "The release is progressing.",
        },
    ]

    processed, report = pipeline.run(emails, as_of="2025-03-04")

    assert [email["category"] for email in processed] == [
        "Urgent & High-Priority Emails",
        "Routine Updates & Check-ins",
    ]
    assert processed[0]["summary"] == "A critical request."
    assert processed[0]["next_action"] == "Review today."
    assert processed[0]["draft_response"].startswith("Subject: Re: Request")
    assert processed[0]["evaluation"]["Relevance"]["score"] == 5
    assert processed[0]["email_body_length"] == len(emails[0]["body"])
    assert sum(email["prompt_tokens_executive_dashboard"] for email in processed) == 30
    assert sum(email["completion_tokens_executive_dashboard"] for email in processed) == 10
    assert sum(email["total_tokens"] for email in processed) > 0
    assert "$5" in llm.calls[0][1]
    assert "Critical emails" in report
    assert len(llm.calls) == 8
    assert progress == [
        "Email 1/2: starting categorization.",
        "Email 1/2: running initial categorization.",
        "Email 1/2: checking links.",
        "Email 1/2: determining final category.",
        "Email 2/2: starting categorization.",
        "Email 2/2: running initial categorization.",
        "Email 2/2: checking links.",
        "Email 2/2: determining final category.",
        "Generating executive dashboard.",
        "Critical email 1/1: generating summary and next step.",
        "Critical email 1/1: drafting reply.",
        "Critical email 1/1: evaluating reply draft.",
    ]


def test_pipeline_returns_empty_report_without_llm_calls():
    llm = FakeLLM()
    pipeline = EmailAssistPipeline(llm, FakeSafetyChecker())

    processed, report = pipeline.run([], as_of="2025-03-04")

    assert processed == []
    assert "No emails matched" in report
    assert llm.calls == []


def test_parse_json_object_accepts_fenced_json_and_rejects_non_object():
    assert parse_json_object('```json\n{"ok": true}\n```') == {"ok": True}

    try:
        parse_json_object("[1, 2]")
    except ValueError as exc:
        assert "JSON object" in str(exc)
    else:
        raise AssertionError("A JSON array should not be accepted as an object.")


def test_calculate_cost_uses_configured_per_million_rates():
    assert calculate_cost(1000, 1000, input_cost_per_million=1, output_cost_per_million=2) == 0.003
