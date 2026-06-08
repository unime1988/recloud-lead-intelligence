"""Optional JobSpy integration for public job-board data.

JobSpy (python-jobspy) is an optional dependency. When it is not installed or
fails (e.g. offline/rate-limited), callers should fall back to other sources.
Only public job data is queried; no logins/CAPTCHAs are bypassed.
"""

import logging

logger = logging.getLogger(__name__)


def is_available() -> bool:
    try:
        import jobspy  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


def scrape_jobs(
    search_term: str,
    location: str | None = None,
    country: str = "india",
    results_wanted: int = 100,
    proxies: list[str] | None = None,
    site_name: list[str] | None = None,
) -> list[dict]:
    """Return a list of normalized job dicts, or [] if unavailable.

    Each dict: {title, company, location, url, posted_date, source,
    description, company_url}. Only public job boards are queried.
    """
    if not is_available():
        logger.info("JobSpy not installed; skipping live job scrape")
        return []
    try:
        from jobspy import scrape_jobs as _scrape

        kwargs = dict(
            site_name=site_name or ["indeed", "linkedin"],
            search_term=search_term,
            location=location or "",
            results_wanted=results_wanted,
            country_indeed=country,
        )
        if proxies:
            kwargs["proxies"] = proxies

        df = _scrape(**kwargs)
        if df is None or len(df) == 0:
            return []
        records = []
        for _, row in df.iterrows():
            records.append(
                {
                    "title": _s(row.get("title")),
                    "company": _s(row.get("company")),
                    "location": _s(row.get("location")),
                    "url": _s(row.get("job_url")),
                    "posted_date": _s(row.get("date_posted")),
                    "source": _s(row.get("site")) or "jobspy",
                    "description": _s(row.get("description")),
                    "company_url": _s(row.get("company_url")),
                }
            )
        return records
    except Exception as exc:  # noqa: BLE001
        logger.warning("JobSpy scrape failed: %s", exc)
        return []


def _s(value) -> str:
    """Coerce a possibly-NaN/None pandas cell to a clean string."""
    if value is None:
        return ""
    text = str(value)
    if text.lower() in ("nan", "none", "nat"):
        return ""
    return text.strip()
