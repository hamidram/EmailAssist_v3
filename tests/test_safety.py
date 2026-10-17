import io
import json
from unittest.mock import patch

from email_assist.safety import SafeBrowsingChecker, extract_urls_from_text


def test_extract_urls_skips_email_addresses_and_deduplicates():
    text = "Contact a@example.com; visit https://example.com/path). or www.test.org."

    assert extract_urls_from_text(text) == [
        "https://example.com/path",
        "http://www.test.org",
    ]


def test_safe_browsing_does_not_claim_urls_are_safe_when_unconfigured():
    checker = SafeBrowsingChecker(api_key=None)

    assert checker.check(["https://example.com"]) == {"status": "not_configured"}
    assert checker.check([]) == {"status": "no_urls"}


def test_safe_browsing_marks_threat_matches_and_other_urls_safe():
    response = io.BytesIO(
        json.dumps(
            {
                "matches": [
                    {
                        "threatEntry": {"url": "https://bad.example"},
                        "threatType": "MALWARE",
                    }
                ]
            }
        ).encode("utf-8")
    )
    checker = SafeBrowsingChecker(api_key="test-key")

    with patch("email_assist.safety.urlopen", return_value=response):
        result = checker.check(["https://bad.example", "https://good.example"])

    assert result == {
        "https://bad.example": "MALWARE",
        "https://good.example": "SAFE",
    }
