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


def is_configured(*, apollo_key: str | None = None, hunter_key: str | None = None) -> bool:
    return bool(_clean(apollo_key) or _clean(hunter_key))


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

    Prefers Hunter (returns emails directly), falls back to Apollo
    (search + enrichment). Both gracefully return None on failure.
    """
    dm = None
    # Hunter first — domain-search returns emails directly.
    if _clean(hunter_key) and domain:
        dm = _hunter_domain_search(domain, titles, hunter_key)  # type: ignore[arg-type]
        if dm:
            return dm

    if _clean(apollo_key) and domain:
        dm = _apollo_search(domain, titles, apollo_key)  # type: ignore[arg-type]
        if dm:
            return dm

    return None


# ---------------------------------------------------------------------------
# Hunter.io
# ---------------------------------------------------------------------------

def _hunter_domain_search(domain: str, titles: list[str], api_key: str) -> dict | None:
    """GET /v2/domain-search — returns emails with name + position."""
    try:
        params: dict = {
            "domain": domain,
            "api_key": api_key,
            "type": "personal",
            "limit": 10,
        }
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
        logger.warning("Hunter domain-search failed for %s: %s", domain, exc)
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

def _apollo_search(domain: str, titles: list[str], api_key: str) -> dict | None:
    """Apollo People Search + People Match to reveal email."""
    try:
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": api_key,
        }
        # Step 1: Search for people at this domain with matching titles.
        search_url = "https://api.apollo.io/api/v1/mixed_people/api_search"
        params: dict = {"per_page": 5}
        if titles:
            for i, t in enumerate(titles[:5]):
                params[f"person_titles[{i}]"] = t
        params["q_organization_domains_list[0]"] = domain

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
        logger.warning("Apollo search failed for %s: %s", domain, exc)
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
