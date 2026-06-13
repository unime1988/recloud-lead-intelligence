"""Keyword-based classification of job postings and company names."""

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
    "interview coordinator",
    "interview scheduler",
    "interview scheduling",
    "assessment coordinator",
    "hiring coordinator",
    "onboarding coordinator",
    "screening coordinator",
    "talent coordinator",
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
    "bulk hiring",
    "mass recruitment",
    "campus",
    "fresher",
    "trainee",
    "intern",
    "associate",
    "executive",
    "customer service",
    "back office",
    "data entry",
    "tele",
    "collections",
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
    "urgently hiring",
    "urgent requirement",
    "urgent opening",
    "immediate start",
    "spot offer",
    "walk in interview",
    "walkin",
    "openings available immediately",
    "fast hiring",
    "need immediately",
]

# ---------------------------------------------------------------------------
# Agency / company-type detection keywords
# ---------------------------------------------------------------------------
RECRUITMENT_AGENCY_KEYWORDS = [
    "staffing",
    "recruitment agency",
    "recruiting agency",
    "placement",
    "manpower",
    "talent solutions",
    "hr services",
    "human resource services",
    "rpo",
    "recruitment process outsourcing",
    "headhunt",
    "headhunting",
    "executive search",
    "job consultancy",
    "employment agency",
    "employment services",
    "talent agency",
    "workforce solutions",
    "teamlease",
    "randstad",
    "adecco",
    "kelly services",
    "robert half",
    "hays",
    "michael page",
    "abc consultants",
    "naukri",
    "quess",
    "genius consultants",
    "ciel hr",
    "ikya",
    "ma foi",
    "careernet",
    "xpheno",
    "foundit",
]

CONSULTING_AGENCY_KEYWORDS = [
    "consulting",
    "consultancy",
    "consultants",
    "it services",
    "technology services",
    "outsourcing",
    "professional services",
    "advisory",
    "solutions provider",
    "systems integrator",
    "managed services",
    "infosys",
    "wipro",
    "tcs",
    "cognizant",
    "hcl",
    "tech mahindra",
    "mphasis",
    "ltimindtree",
    "l&t infotech",
    "hexaware",
    "cyient",
    "mindtree",
    "niit technologies",
    "zensar",
    "coforge",
    "persistent systems",
    "birlasoft",
]

SOURCING_AGENCY_KEYWORDS = [
    "sourcing",
    "talent sourcing",
    "candidate sourcing",
    "research firm",
    "search firm",
    "executive search",
    "headhunter",
    "sourcing partner",
    "sourcing agency",
    "sourcing solutions",
    "talent mapping",
    "talent research",
    "recruitment research",
]


def _matches(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in keywords if k)


def classify_company_type(company_name: str) -> dict[str, bool]:
    """Classify a company name into agency types."""
    return {
        "is_recruitment_agency": _matches(company_name, RECRUITMENT_AGENCY_KEYWORDS),
        "is_consulting_agency": _matches(company_name, CONSULTING_AGENCY_KEYWORDS),
        "is_sourcing_agency": _matches(company_name, SOURCING_AGENCY_KEYWORDS),
    }


def matches_company_type_filter(company_name: str, company_type: str) -> bool:
    """Return True if company_name matches the requested company_type filter."""
    if company_type == "all":
        return True

    ct = classify_company_type(company_name)

    if company_type == "recruitment":
        return ct["is_recruitment_agency"]
    if company_type == "consulting":
        return ct["is_consulting_agency"]
    if company_type == "sourcing":
        return ct["is_sourcing_agency"]
    if company_type == "recruitment_and_consulting":
        return ct["is_recruitment_agency"] or ct["is_consulting_agency"]
    return True


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
