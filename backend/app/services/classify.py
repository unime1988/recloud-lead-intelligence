"""Keyword-based classification of job postings into hiring signals."""

DEFAULT_RECRUITER_KEYWORDS = [
    "recruiter",
    "talent acquisition",
    "ta specialist",
    "talent partner",
    "technical recruiter",
    "sourcer",
]
DEFAULT_TA_COORDINATOR_KEYWORDS = [
    "ta coordinator",
    "recruitment coordinator",
    "recruiting coordinator",
    "recruitment ops",
    "recruiting operations",
    "talent operations",
    "people ops",
]
DEFAULT_HIGH_VOLUME_KEYWORDS = [
    "sales",
    "support",
    "customer support",
    "bpo",
    "operations",
    "telecaller",
    "call center",
    "field",
    "delivery",
    "warehouse",
]
URGENT_KEYWORDS = [
    "urgent",
    "immediate",
    "immediately",
    "asap",
    "hiring now",
    "walk-in",
    "walk in",
    "quick joiner",
    "immediate joiner",
]


def _matches(title: str, keywords: list[str]) -> bool:
    t = title.lower()
    return any(k.lower() in t for k in keywords if k)


def classify_title(title: str, campaign_keywords: dict) -> dict:
    recruiter_kw = DEFAULT_RECRUITER_KEYWORDS + campaign_keywords.get("recruiter_keywords", [])
    high_vol_kw = DEFAULT_HIGH_VOLUME_KEYWORDS + campaign_keywords.get("high_volume_role_keywords", [])

    is_ta_coordinator = _matches(title, DEFAULT_TA_COORDINATOR_KEYWORDS)
    # A coordinator/ops role is also a TA-team hire but tracked separately.
    is_recruiter = _matches(title, recruiter_kw) and not is_ta_coordinator
    is_high_volume = _matches(title, high_vol_kw)
    is_urgent = _matches(title, URGENT_KEYWORDS)

    return {
        "is_recruiter_role": is_recruiter,
        "is_ta_coordinator": is_ta_coordinator,
        "is_high_volume_role": is_high_volume,
        "is_urgent": is_urgent,
    }
