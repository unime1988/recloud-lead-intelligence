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
) -> list[dict]:
    """Return a list of normalized job dicts, or [] if unavailable.

    Each dict: {title, company, location, url, posted_date, source}.
    """
    if not is_available():
        logger.info("JobSpy not installed; skipping live job scrape")
        return []
    try:
        from jobspy import scrape_jobs as _scrape

        df = _scrape(
            site_name=["indeed", "linkedin"],
            search_term=search_term,
            location=location or "",
            results_wanted=results_wanted,
            country_indeed=country,
        )
        records = []
        for _, row in df.iterrows():
            records.append(
                {
                    "title": str(row.get("title", "")),
                    "company": str(row.get("company", "")),
                    "location": str(row.get("location", "")),
                    "url": str(row.get("job_url", "")),
                    "posted_date": str(row.get("date_posted", "")),
                    "source": str(row.get("site", "jobspy")),
                }
            )
        return records
    except Exception as exc:  # noqa: BLE001
        logger.warning("JobSpy scrape failed: %s", exc)
        return []
