"""Optional Firecrawl integration for scraping public career pages.

Only public pages are scraped. Respect robots.txt and rate limits; do not
bypass logins, CAPTCHAs, or paywalls. No-ops gracefully without an API key.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


def is_configured(api_key: str | None) -> bool:
    return bool(api_key) and not str(api_key).startswith("replace_with")


def scrape_careers_page(url: str, api_key: str | None, base_url: str) -> str | None:
    """Return markdown/text of a public career page, or None on failure."""
    if not is_configured(api_key):
        logger.info("Firecrawl not configured; skipping career-page scrape for %s", url)
        return None
    try:
        resp = httpx.post(
            f"{base_url.rstrip('/')}/v1/scrape",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown"]},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("markdown")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Firecrawl scrape failed for %s: %s", url, exc)
        return None
