"""Decision-maker enrichment via Apollo.io and Hunter.io.

Finds a decision-maker (name + title + email) for a given company domain
using the campaign's target titles. Falls back gracefully when neither
service is configured or when an API call fails.
"""

import logging
import re
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0

# Job-board / aggregator hosts that are never a company's real domain. When the
# only "domain" we have is one of these (common with live JobSpy data, whose
# company_url points at the board's company page), we resolve contacts by
# company name instead.
_JOB_BOARD_DOMAINS = (
    "indeed.com",
    "linkedin.com",
    "glassdoor.com",
    "ziprecruiter.com",
    "naukri.com",
    "monster.com",
    "simplyhired.com",
    "google.com",
    "bing.com",
)


def is_configured(*, apollo_key: str | None = None, hunter_key: str | None = None) -> bool:
    return bool(_clean(apollo_key) or _clean(hunter_key))


def _is_job_board(domain: str) -> bool:
    d = (domain or "").lower()
    return any(d == b or d.endswith("." + b) for b in _JOB_BOARD_DOMAINS)


def domain_from_url(url: str) -> str:
    """Extract a bare domain from a URL or company name guess."""
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    host = parsed.hostname or ""
    host = re.sub(r"^www\.", "", host)
    return host


def find_decision_maker(
    company_name: str,
    domain: str,
    titles: list[str],
    *,
    apollo_key: str | None = None,
    hunter_key: str | None = None,
) -> dict | None:
    """Return ``{name, title, email}`` or ``None``.

    Queries both Hunter and Apollo (when configured) and returns the
    first result that includes an email. This maximises coverage:
    Hunter resolves by company name even without a real domain, while
    Apollo searches by domain or company name.
    """
    # A job-board host (indeed.com, linkedin.com, ...) is not the company's real
    # domain, so don't use it for a domain lookup.
    usable_domain = domain if (domain and not _is_job_board(domain)) else ""

    # Try Hunter — domain-search returns emails directly, and also accepts a
    # company name (which it resolves to the real domain) when we lack one.
    hunter_result = None
    if _clean(hunter_key) and (usable_domain or company_name):
        hunter_result = _hunter_domain_search(usable_domain, company_name, titles, hunter_key)  # type: ignore[arg-type]

    # Try Apollo — people search by domain or company name.
    apollo_result = None
    if _clean(apollo_key) and (usable_domain or company_name):
        apollo_result = _apollo_search(usable_domain, company_name, titles, apollo_key)  # type: ignore[arg-type]

    # Prefer whichever result has an email; if both do, prefer the one
    # with a better title match (has a title set).
    candidates = [r for r in (hunter_result, apollo_result) if r and r.get("email")]
    if not candidates:
        # Return any result even without email
        return hunter_result or apollo_result or None

    # Prefer the candidate that has both a name and a title
    candidates.sort(key=lambda r: (bool(r.get("title")), bool(r.get("name"))), reverse=True)
    return candidates[0]


# ---------------------------------------------------------------------------
# Hunter.io
# ---------------------------------------------------------------------------

def _hunter_domain_search(
    domain: str, company_name: str, titles: list[str], api_key: str
) -> dict | None:
    """GET /v2/domain-search — returns emails with name + position.

    Queries by ``domain`` when we have a real one, otherwise by ``company``
    name (Hunter resolves it to the company's domain).
    """
    try:
        params: dict = {
            "api_key": api_key,
            "type": "personal",
            "limit": 10,
        }
        if domain:
            params["domain"] = domain
        elif company_name:
            params["company"] = company_name
        else:
            return None
        resp = httpx.get(
            "https://api.hunter.io/v2/domain-search",
            params=params,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        emails = resp.json().get("data", {}).get("emails", [])
        if not emails:
            return None

        best = _pick_best_match(emails, titles)
        if not best:
            return None

        first = best.get("first_name", "")
        last = best.get("last_name", "")
        name = f"{first} {last}".strip() or None
        return {
            "name": name,
            "title": best.get("position") or None,
            "email": best.get("value") or None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Hunter domain-search failed for %s: %s", domain or company_name, exc
        )
        return None


def _pick_best_match(emails: list[dict], titles: list[str]) -> dict | None:
    """Pick the email entry whose position best matches the target titles."""
    title_lower = [t.lower() for t in titles if t]

    scored: list[tuple[int, int, dict]] = []
    for entry in emails:
        pos = (entry.get("position") or "").lower()
        conf = entry.get("confidence", 0) or 0
        title_score = 0
        for kw in title_lower:
            if kw in pos:
                title_score = 10
                break
        # Prefer HR/TA/People positions even if not in target titles.
        for kw in ("talent", "recruit", "people", "hr", "human resource"):
            if kw in pos:
                title_score = max(title_score, 5)
                break
        scored.append((title_score, conf, entry))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    if scored:
        return scored[0][2]
    return None


# ---------------------------------------------------------------------------
# Apollo.io
# ---------------------------------------------------------------------------

def _apollo_search(
    domain: str, company_name: str, titles: list[str], api_key: str
) -> dict | None:
    """Apollo People Search + People Match to reveal email.

    Searches by domain when available, otherwise by company name.
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": api_key,
        }
        # Step 1: Search for people at this domain/company with matching titles.
        search_url = "https://api.apollo.io/api/v1/mixed_people/api_search"
        params: dict = {"per_page": 5}
        if titles:
            for i, t in enumerate(titles[:5]):
                params[f"person_titles[{i}]"] = t
        if domain:
            params["q_organization_domains_list[0]"] = domain
        elif company_name:
            params["q_organization_name"] = company_name
        else:
            return None

        resp = httpx.post(search_url, headers=headers, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        people = resp.json().get("people", [])
        if not people:
            return None

        person = people[0]
        first = person.get("first_name", "")
        last = person.get("last_name", "")
        name = f"{first} {last}".strip() or None
        title = person.get("title") or None
        person_id = person.get("id")

        # Step 2: Reveal email via people/match.
        email = person.get("email") or None
        if not email and person_id:
            email = _apollo_reveal_email(person_id, headers)

        return {"name": name, "title": title, "email": email}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Apollo search failed for %s: %s", domain or company_name, exc)
        return None


def _apollo_reveal_email(person_id: str, headers: dict) -> str | None:
    """POST /api/v1/people/match to reveal email for a known person."""
    try:
        resp = httpx.post(
            "https://api.apollo.io/api/v1/people/match",
            headers=headers,
            json={"id": person_id, "reveal_personal_emails": False},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        person = resp.json().get("person", {})
        return person.get("email") or None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Apollo email reveal failed for person %s: %s", person_id, exc)
        return None


def _clean(value: str | None) -> str:
    if not value or str(value).startswith(("replace_with", "replace_if")):
        return ""
    return value
