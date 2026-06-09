"""Build company lead dicts from live job data (JobSpy) and contact enrichment.

Returns the same dict shape as ``sample_data.generate_companies`` so the
research pipeline treats live and sample data identically. Falls back
gracefully — callers should check for an empty list and fall back to
sample data when needed.
"""

import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.services import enrichment, jobspy_service
from app.services.classify import URGENT_KEYWORDS, classify_title

logger = logging.getLogger(__name__)

STALE_DAYS = 30


def is_enabled(eff: dict) -> bool:
    """Check whether live job scraping is configured and available."""
    return bool(eff.get("jobspy_enabled")) and jobspy_service.is_available()


def build_companies(
    campaign,
    eff: dict,
    *,
    limit: int = 10,
) -> list[dict]:
    """Scrape live jobs, group by company, compute signals, enrich contacts.

    Returns a list of company dicts (same shape as ``sample_data``) sorted
    by signal strength (descending). Returns ``[]`` when no usable data.
    """
    all_jobs = _scrape_jobs_for_campaign(campaign, eff)
    if not all_jobs:
        return []

    grouped = _group_by_company(all_jobs)
    campaign_kw = {
        "recruiter_keywords": campaign.recruiter_keywords or [],
        "high_volume_role_keywords": campaign.high_volume_role_keywords or [],
    }

    companies: list[dict] = []
    for company_name, jobs in grouped.items():
        comp = _compute_signals(company_name, jobs, campaign, campaign_kw, eff)
        companies.append(comp)

    companies.sort(key=lambda c: _rough_score(c), reverse=True)
    companies = companies[:limit]

    # Enrich decision-makers for top companies (rate-conscious: limit calls).
    _enrich_decision_makers(companies, campaign, eff)

    return companies


# ---------------------------------------------------------------------------
# Job scraping
# ---------------------------------------------------------------------------

def _scrape_jobs_for_campaign(campaign, eff: dict) -> list[dict]:
    """Collect jobs from JobSpy using campaign keywords + region."""
    search_terms = _build_search_terms(campaign)
    location = campaign.region or ""
    country = eff.get("jobspy_country", "india")
    results_wanted = int(eff.get("jobspy_results_limit", 100))
    proxies_raw = eff.get("jobspy_proxies", "")
    proxies = [p.strip() for p in proxies_raw.split(",") if p.strip()] if proxies_raw else None

    all_jobs: list[dict] = []
    seen_urls: set[str] = set()
    for term in search_terms:
        jobs = jobspy_service.scrape_jobs(
            search_term=term,
            location=location,
            country=country,
            results_wanted=results_wanted,
            proxies=proxies,
        )
        for j in jobs:
            url = j.get("url", "")
            key = url or f"{j.get('title','')}__{j.get('company','')}__{j.get('location','')}"
            if key not in seen_urls:
                seen_urls.add(key)
                all_jobs.append(j)

    logger.info("JobSpy returned %d unique jobs across %d search terms", len(all_jobs), len(search_terms))
    return all_jobs


def _build_search_terms(campaign) -> list[str]:
    """Derive 1–3 search terms from campaign configuration."""
    terms: list[str] = []
    if campaign.job_keywords:
        terms.extend(campaign.job_keywords[:3])
    if not terms and campaign.industry:
        terms.append(f"{campaign.industry} jobs")
    if not terms:
        terms.append("hiring")
    return terms


# ---------------------------------------------------------------------------
# Grouping + signal computation
# ---------------------------------------------------------------------------

def _group_by_company(jobs: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for j in jobs:
        name = (j.get("company") or "").strip()
        if not name:
            continue
        # Normalize: lowercase for grouping, store original.
        key = re.sub(r"\s+", " ", name.lower())
        groups[key].append(j)
    return dict(groups)


def _compute_signals(
    company_key: str,
    jobs: list[dict],
    campaign,
    campaign_kw: dict,
    eff: dict,
) -> dict:
    """Build a company dict from a group of jobs."""
    company_name = jobs[0].get("company", company_key).strip()
    total_open = len(jobs)

    recruiter_count = 0
    ta_coord_count = 0
    high_vol_count = 0
    urgent_any = False
    locations: set[str] = set()
    stale_any = False
    company_url = ""

    sample_jobs: list[dict] = []
    for j in jobs:
        title = j.get("title", "")
        flags = classify_title(title, campaign_kw)
        if flags["is_recruiter_role"]:
            recruiter_count += 1
        if flags["is_ta_coordinator"]:
            ta_coord_count += 1
        if flags["is_high_volume_role"]:
            high_vol_count += 1

        # Urgent: check title + description.
        is_urgent = flags["is_urgent"]
        if not is_urgent:
            desc = (j.get("description") or "").lower()
            is_urgent = any(kw.lower() in desc for kw in URGENT_KEYWORDS)
        if is_urgent:
            urgent_any = True

        loc = (j.get("location") or "").strip()
        if loc:
            locations.add(loc)

        # Stale detection.
        is_stale = _is_stale(j.get("posted_date"))
        if is_stale:
            stale_any = True

        if not company_url:
            company_url = j.get("company_url", "") or ""

        sample_jobs.append({
            "title": title,
            "location": loc,
            "posted_date": j.get("posted_date", ""),
            "stale": is_stale,
            "urgent": is_urgent,
            "url": j.get("url", ""),
        })

    domain = enrichment.domain_from_url(company_url) if company_url else ""
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    website = company_url or (f"https://{slug}.com" if slug else "")
    careers_url = f"{website.rstrip('/')}/careers" if website else ""

    return {
        "company_name": company_name,
        "website": website,
        "careers_url": careers_url,
        "industry": campaign.industry or "",
        "region": campaign.region or "",
        "employee_count": None,
        "total_open_jobs": total_open,
        "recruiter_jobs_open": recruiter_count,
        "ta_coordinator_jobs": ta_coord_count,
        "high_volume_role_jobs": high_vol_count,
        "has_urgent_hiring": urgent_any,
        "has_multiple_locations": len(locations) > 1,
        "has_stale_jobs": stale_any,
        "locations": sorted(locations),
        "decision_maker": None,
        "sample_jobs": sample_jobs[:20],
        "source": "jobspy",
        "_domain": domain,
    }


def _is_stale(posted_date_str: str | None) -> bool:
    if not posted_date_str:
        return False
    try:
        dt = datetime.fromisoformat(str(posted_date_str).strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt) > timedelta(days=STALE_DAYS)
    except (ValueError, TypeError):
        return False


def _rough_score(comp: dict) -> int:
    """Quick heuristic for sorting before formal scoring."""
    s = 0
    total = comp["total_open_jobs"]
    if total >= 100:
        s += 5
    elif total >= 50:
        s += 3
    elif total >= 20:
        s += 2
    s += min(comp["recruiter_jobs_open"], 3) * 2
    s += min(comp["ta_coordinator_jobs"], 2) * 3
    s += 3 if comp["high_volume_role_jobs"] >= 5 else (1 if comp["high_volume_role_jobs"] >= 1 else 0)
    if comp["has_urgent_hiring"]:
        s += 1
    if comp["has_multiple_locations"]:
        s += 2
    return s


# ---------------------------------------------------------------------------
# Decision-maker enrichment
# ---------------------------------------------------------------------------

def _enrich_decision_makers(companies: list[dict], campaign, eff: dict) -> None:
    """Attempt to find a decision-maker for each company via Apollo/Hunter."""
    apollo_key = eff.get("apollo_api_key", "")
    hunter_key = eff.get("hunter_api_key", "")
    if not enrichment.is_configured(apollo_key=apollo_key, hunter_key=hunter_key):
        logger.info("No contact enrichment keys configured; skipping decision-maker lookup.")
        return

    titles = campaign.target_decision_maker_titles or [
        "Head of Talent Acquisition",
        "VP People",
        "Director of HR",
        "Talent Acquisition Manager",
    ]

    for comp in companies:
        domain = comp.get("_domain") or enrichment.domain_from_url(comp.get("website", ""))
        # Even with no usable domain we can still resolve contacts by company
        # name via Hunter, so always attempt enrichment.
        try:
            dm = enrichment.find_decision_maker(
                comp["company_name"],
                domain,
                titles,
                apollo_key=apollo_key,
                hunter_key=hunter_key,
            )
            if dm:
                comp["decision_maker"] = dm
        except Exception as exc:  # noqa: BLE001
            logger.warning("Enrichment failed for %s: %s", comp["company_name"], exc)
