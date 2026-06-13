"""Deterministic sample-company generator.

Used as the research fallback when live integrations (JobSpy/Firecrawl) are
not configured, so the full pipeline (signals -> scoring -> AI drafts ->
dashboard) works out of the box for local development. Sample leads are
clearly marked with source "sample".
"""

import random

INDUSTRIES = ["IT Services", "BPO", "Fintech", "E-commerce", "Staffing", "SaaS", "Logistics"]
REGIONS = ["India", "Bengaluru, India", "Mumbai, India", "Pune, India", "Hyderabad, India"]
CITY_POOL = ["Bengaluru", "Mumbai", "Pune", "Hyderabad", "Chennai", "Delhi NCR", "Remote"]

DM_TITLES = [
    "Head of Talent Acquisition",
    "VP People",
    "Director of HR",
    "Talent Acquisition Manager",
    "Chief People Officer",
]
FIRST = ["Priya", "Arjun", "Neha", "Rahul", "Sneha", "Vikram", "Anita", "Karan", "Divya", "Rohit"]
LAST = ["Sharma", "Patel", "Iyer", "Reddy", "Nair", "Gupta", "Mehta", "Rao", "Verma", "Kapoor"]


def _slug(name: str) -> str:
    return "".join(c for c in name.lower() if c.isalnum())


def _sample_jobs(rng: random.Random, recruiter: int, ta_coord: int, high_vol: int, urgent: bool, locations: list[str]) -> list[dict]:
    jobs: list[dict] = []
    for i in range(recruiter):
        jobs.append({"title": rng.choice(["Senior Technical Recruiter", "Talent Acquisition Specialist", "Recruiter"]),
                     "location": rng.choice(locations), "posted_date": "2026-05-20", "stale": False, "urgent": urgent and i == 0})
    for _ in range(ta_coord):
        jobs.append({"title": rng.choice(["Recruitment Coordinator", "Talent Operations Associate", "Recruiting Ops Specialist"]),
                     "location": rng.choice(locations), "posted_date": "2026-05-22", "stale": False, "urgent": False})
    for i in range(min(high_vol, 6)):
        jobs.append({"title": rng.choice(["Sales Executive", "Customer Support Associate", "BPO Voice Process", "Operations Executive", "Field Sales Manager"]),
                     "location": rng.choice(locations), "posted_date": "2026-04-10" if i % 3 == 0 else "2026-05-18",
                     "stale": i % 3 == 0, "urgent": urgent and i == 1})
    if not jobs:
        jobs.append({"title": "Software Engineer", "location": locations[0], "posted_date": "2026-05-25", "stale": False, "urgent": False})
    return jobs


def generate_companies(campaign, count: int = 10) -> list[dict]:
    """Return a list of synthetic company dicts spanning the score spectrum."""
    rng = random.Random(campaign.id * 1000 + 7)
    industry = campaign.industry or rng.choice(INDUSTRIES)
    region = campaign.region or rng.choice(REGIONS)

    # Archetypes (total_open, recruiter, ta_coord, high_vol, urgent, multi_loc, stale, has_dm)
    archetypes = [
        (140, 3, 2, 45, True, True, True, True),   # Very Hot
        (110, 2, 1, 30, True, True, False, True),  # Very Hot / High
        (75, 2, 1, 20, True, True, True, True),    # High
        (60, 1, 1, 12, False, True, False, True),  # High
        (55, 1, 0, 10, True, False, False, True),  # Medium/High
        (35, 1, 0, 6, False, True, False, False),  # Medium
        (28, 1, 0, 3, False, False, False, True),  # Medium
        (22, 0, 0, 4, True, False, False, False),  # Low/Medium
        (14, 0, 0, 2, False, False, False, False), # Low
        (6, 0, 0, 0, False, False, False, False),  # Low
    ]

    company_names = [
        "NimbusTech Solutions", "BrightHire Labs", "ScaleForce Systems", "Apex Talent Group",
        "Velocity BPO", "CloudNova Software", "PrimeEdge Services", "Quantum Staffing",
        "Orbit Commerce", "Lumen Fintech", "Stride Logistics", "Pioneer Digital",
    ]
    rng.shuffle(company_names)

    companies: list[dict] = []
    for i in range(min(count, len(archetypes))):
        total, rec, tac, hv, urgent, multi, stale, has_dm = archetypes[i]
        name = company_names[i % len(company_names)]
        num_locations = rng.randint(2, 4) if multi else 1
        locations = rng.sample(CITY_POOL, num_locations)
        dm = None
        if has_dm:
            dm = {
                "name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                "title": rng.choice(DM_TITLES),
                "email": f"{_slug(rng.choice(FIRST))}@{_slug(name)}.com",
            }
        companies.append(
            {
                "company_name": name,
                "website": f"https://{_slug(name)}.com",
                "careers_url": f"https://{_slug(name)}.com/careers",
                "industry": industry,
                "region": region,
                "employee_count": max(campaign.min_employee_count, rng.choice([80, 150, 300, 600, 1200, 2500])),
                "total_open_jobs": total,
                "recruiter_jobs_open": rec,
                "ta_coordinator_jobs": tac,
                "high_volume_role_jobs": hv,
                "has_urgent_hiring": urgent,
                "has_multiple_locations": multi,
                "has_stale_jobs": stale,
                "locations": locations,
                "decision_maker": dm,
                "sample_jobs": _sample_jobs(rng, rec, tac, hv, urgent, locations),
                "source": "sample",
            }
        )
    return companies
