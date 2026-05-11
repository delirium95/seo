import json

import anthropic

from config import settings
from models import GeneratedMeta, ScrapedPage

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = """You are an expert SEO copywriter specializing in affiliate casino/gambling content.
You write precise, conversion-focused meta tags that rank well and drive clicks.
You always respond with valid JSON only — no markdown, no explanation."""

_USER_TEMPLATE = """
Analyze these competitor meta tags and generate optimized SEO content.

KEYWORD: {keyword}
TARGET LANGUAGE: {language}

COMPETITORS:
{competitors_block}

RULES:
1. H1 and Meta Title MUST start with the exact keyword: "{keyword}"
2. FORBIDDEN words: Discover, Thrilling, Enjoy, Excitement, "Dive into", Experience
3. NO emojis anywhere
4. Focus on bonuses, payout speed, or unique value propositions
5. Meta Title: 40-60 characters
6. Meta Description: under 160 characters
7. Capitalize every word in Title; capitalize sentence starts in Description
8. Write in {language} language (ISO 639-1 code)
9. Avoid template phrases and clichés

Return ONLY this JSON:
{{
  "h1": "...",
  "meta_title": "...",
  "meta_description": "..."
}}
"""


def _build_competitors_block(pages: list[ScrapedPage]) -> str:
    lines = []
    for i, page in enumerate(pages, 1):
        lines.append(f"#{i} (position {page.position}): {page.url}")
        lines.append(f"  H1: {page.h1}")
        lines.append(f"  Title: {page.meta_title}")
        lines.append(f"  Description: {page.meta_description}")
        if page.site_structure:
            lines.append(f"  Structure: {' | '.join(page.site_structure[:5])}")
        lines.append("")
    return "\n".join(lines)


def generate_meta(keyword: str, language: str, pages: list[ScrapedPage]) -> GeneratedMeta:
    competitors_block = _build_competitors_block(pages)
    user_message = _USER_TEMPLATE.format(
        keyword=keyword,
        language=language,
        competitors_block=competitors_block,
    )

    message = _client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    data = json.loads(raw)
    return GeneratedMeta(
        h1=data["h1"],
        meta_title=data["meta_title"],
        meta_description=data["meta_description"],
    )
