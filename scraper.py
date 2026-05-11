import httpx
from bs4 import BeautifulSoup

from models import ScrapedPage, SerpResult

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_TIMEOUT = 15


def _extract(soup: BeautifulSoup, url: str) -> tuple[str, str, str, list[str]]:
    h1_tag = soup.find("h1")
    h1 = h1_tag.get_text(strip=True) if h1_tag else ""

    title_tag = soup.find("title")
    meta_title = title_tag.get_text(strip=True) if title_tag else ""

    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    meta_description = desc_tag.get("content", "").strip() if desc_tag else ""

    # Collect h2/h3 headings as site structure
    structure: list[str] = []
    for tag in soup.find_all(["h2", "h3"])[:10]:
        text = tag.get_text(strip=True)
        if text:
            structure.append(f"{tag.name.upper()}: {text}")

    return h1, meta_title, meta_description, structure


def scrape_page(result: SerpResult) -> ScrapedPage:
    try:
        resp = httpx.get(result.url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        h1, meta_title, meta_description, structure = _extract(soup, result.url)
        return ScrapedPage(
            url=result.url,
            position=result.position,
            h1=h1,
            meta_title=meta_title,
            meta_description=meta_description,
            site_structure=structure,
        )
    except Exception as exc:
        return ScrapedPage(
            url=result.url,
            position=result.position,
            h1="",
            meta_title="",
            meta_description="",
            error=str(exc),
        )


def collect_affiliate_pages(
    serp_results: list[SerpResult],
    target: int = 3,
) -> tuple[list[ScrapedPage], list[ScrapedPage]]:
    """
    Returns (successful_pages, failed_pages).
    Stops collecting successful pages once `target` is reached,
    but never goes beyond the provided serp_results (already capped at TOP-10).
    """
    successful: list[ScrapedPage] = []
    failed: list[ScrapedPage] = []

    for result in serp_results:
        if len(successful) >= target:
            break
        page = scrape_page(result)
        if page.error:
            failed.append(page)
        else:
            successful.append(page)

    return successful, failed
