import httpx

from config import settings
from models import SerpResult

_SERP_API_URL = "https://serpapi.com/search"

# Known non-affiliate domains to skip (official brand sites, aggregators, etc.)
_EXCLUDED_DOMAINS = {
    "wikipedia.org",
    "google.com",
    "youtube.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "trustpilot.com",
    "app-store.com",
    "play.google.com",
    "apps.apple.com",
}

# Keywords in URL/domain/title that suggest an affiliate review site
_AFFILIATE_SIGNALS = [
    "review",
    "casino",
    "bonus",
    "bet",
    "gambling",
    "slot",
    "poker",
    "aviator",
    "1win",
    "novibet",
    "rating",
    "top",
    "best",
    "compare",
]


def _is_affiliate(result: dict) -> bool:
    url = result.get("link", "").lower()
    title = result.get("title", "").lower()
    snippet = result.get("snippet", "").lower()
    combined = url + title + snippet
    return any(signal in combined for signal in _AFFILIATE_SIGNALS)


def get_serp_results(keyword: str, geo: str) -> list[SerpResult]:
    """Return up to top_n organic results filtered to affiliate sites."""
    params = {
        "q": keyword,
        "gl": geo.lower(),
        "hl": "en",
        "num": settings.serp_top_n,
        "api_key": settings.serp_api_key,
        "engine": "google",
    }
    response = httpx.get(_SERP_API_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    organic = data.get("organic_results", [])
    results: list[SerpResult] = []

    for item in organic:
        position = item.get("position", 0)
        if position > settings.serp_top_n:
            break
        url = item.get("link", "")
        domain = url.split("/")[2] if url.startswith("http") else ""
        if any(excl in domain for excl in _EXCLUDED_DOMAINS):
            continue
        if not _is_affiliate(item):
            continue
        results.append(
            SerpResult(
                position=position,
                url=url,
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
            )
        )

    return results[: settings.serp_top_n]
