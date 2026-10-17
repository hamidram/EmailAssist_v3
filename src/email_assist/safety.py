from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

URL_PATTERN = re.compile(
    r"\b(?:https?://|ftp://|www\.)[^\s<>\"']+"
    r"|\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s<>\"']*)?",
    re.IGNORECASE,
)
TRAILING_URL_PUNCTUATION = ".,;:!?)]}"
THREAT_TYPES = (
    "MALWARE",
    "SOCIAL_ENGINEERING",
    "UNWANTED_SOFTWARE",
    "POTENTIALLY_HARMFUL_APPLICATION",
)
SAFE_BROWSING_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


def extract_urls_from_text(text: str) -> list[str]:
    found: list[str] = []
    for match in URL_PATTERN.finditer(text):
        if match.start() > 0 and text[match.start() - 1] == "@":
            continue
        candidate = match.group(0).rstrip(TRAILING_URL_PUNCTUATION)
        if not candidate:
            continue
        if not candidate.lower().startswith(("http://", "https://", "ftp://")):
            candidate = f"http://{candidate}"
        if candidate not in found:
            found.append(candidate)
    return found


class SafeBrowsingChecker:
    def __init__(self, api_key: str | None, timeout: float = 10.0) -> None:
        self._api_key = api_key
        self._timeout = timeout

    def check(self, urls: list[str]) -> dict[str, str]:
        if not urls:
            return {"status": "no_urls"}
        if not self._api_key:
            return {"status": "not_configured"}

        results: dict[str, str] = {}
        for start in range(0, len(urls), 500):
            batch = urls[start : start + 500]
            matches = self._request_batch(batch)
            results.update({url: "SAFE" for url in batch})
            for match in matches:
                url = match.get("threatEntry", {}).get("url")
                if url in results:
                    results[url] = match.get("threatType", "UNKNOWN_THREAT")
        return results

    def _request_batch(self, urls: list[str]) -> list[dict[str, Any]]:
        query = urlencode({"key": self._api_key})
        request = Request(
            f"{SAFE_BROWSING_ENDPOINT}?{query}",
            data=json.dumps(
                {
                    "client": {
                        "clientId": "email-assist",
                        "clientVersion": "0.1.0",
                    },
                    "threatInfo": {
                        "threatTypes": list(THREAT_TYPES),
                        "platformTypes": ["ANY_PLATFORM"],
                        "threatEntryTypes": ["URL"],
                        "threatEntries": [{"url": url} for url in urls],
                    },
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError("Google Safe Browsing request failed.") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("Google Safe Browsing returned invalid JSON.") from exc

        matches = payload.get("matches", [])
        if not isinstance(matches, list):
            raise ValueError("Google Safe Browsing returned an invalid matches list.")
        return matches
