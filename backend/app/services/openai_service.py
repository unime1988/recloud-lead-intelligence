"""OpenAI-compatible AI generation for outreach drafts.

Falls back to deterministic templates when no API key is configured so the
app produces useful drafts out of the box. Outreach is generated as DRAFTS
only; nothing is auto-sent.

NEW TEMPLATE SYSTEM (v2):
- Product name "RACHEL" mentioned by name with specific capability
- Industry-specific case studies auto-selected from 5 mapped types
- Dual CTAs: reply "interested" + landing page link
- Peer tone maintained (short, no jargon)
"""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

AI_FIELDS = [
    "pain_hypothesis",
    "bandwidth_pressure",
    "buyer_persona",
    "outreach_angle",
    "cold_email",
    "linkedin_message",
    "whatsapp_message",
    "case_study_used",
]

# ---------------------------------------------------------------------------
# Industry-specific case studies (auto-selected based on lead industry)
# ---------------------------------------------------------------------------
_CASE_STUDIES = {
    "staffing": {
        "label": "Staffing agencies",
        "headline": "3x placements without extra recruiters",
        "detail": (
            "RACHEL helped a staffing agency triple placements "
            "in 90 days without adding a single recruiter."
        ),
    },
    "bpo": {
        "label": "BPO / ITES",
        "headline": "6-day shortlists to 24 hours",
        "detail": (
            "RACHEL cut shortlist turnaround from 6 days to 24 hours "
            "for a 2,000-seat BPO."
        ),
    },
    "it_services": {
        "label": "IT services",
        "headline": "28 hrs/week to 8 hrs/week recruiter admin",
        "detail": (
            "RACHEL reduced recruiter admin time from 28 hrs/week to 8 hrs/week "
            "for a 500-person IT services firm."
        ),
    },
    "enterprise": {
        "label": "Enterprise / GCC",
        "headline": "55% lower cost-per-qualified-CV",
        "detail": (
            "RACHEL dropped cost-per-qualified-CV by 55% "
            "for a Fortune 500 GCC in India."
        ),
    },
    "startup": {
        "label": "Startups",
        "headline": "Filled seats 70% faster without adding headcount",
        "detail": (
            "RACHEL helped a Series B startup fill seats 70% faster "
            "with zero additional recruiters."
        ),
    },
}

_INDUSTRY_KEYWORDS = {
    "staffing": ["staffing", "recruitment agency", "placement", "contract staffing"],
    "bpo": ["bpo", "ites", "call center", "voice process", "customer support", "back office"],
    "it_services": ["it services", "software services", "consulting", "system integrator", "si"],
    "enterprise": ["enterprise", "gcc", "global capability center", "fortune", "mnc", "multinational"],
    "startup": ["startup", "early-stage", "seed", "series a", "series b", "unicorn"],
}

_PRODUCT_NAME = settings.product_name
_PRODUCT_URL = settings.product_landing_url
_PRODUCT_DESC = settings.product_description


def _detect_industry_bucket(industry: str | None) -> str:
    """Map free-text industry to one of the 5 case-study buckets."""
    if not industry:
        return "startup"
    text = industry.lower()
    for bucket, keywords in _INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return bucket
    # Default: if high volume roles → BPO-ish, else startup
    return "bpo" if any(k in text for k in ["outsourcing", "process", "operations"]) else "startup"


def _get_case_study(lead: dict) -> dict:
    """Return the matched case study for this lead."""
    bucket = _detect_industry_bucket(lead.get("industry"))
    return _CASE_STUDIES[bucket]


# ---------------------------------------------------------------------------
# AI prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(lead: dict) -> str:
    signals = ", ".join(s.get("label", "") for s in lead.get("signals", [])) or "general hiring activity"
    cs = _get_case_study(lead)

    return (
        "You are an SDR assistant for RACHEL, an AI recruitment automation product. "
        "Given the company hiring signals below, produce concise, non-pushy outreach DRAFTS.\n\n"
        "RULES:\n"
        "1. Mention RACHEL by name and specific capability.\n"
        f"2. Use this matched case study: {cs['label']} → {cs['headline']}\n"
        "3. Include TWO CTAs in every message:\n"
        f"   a) Reply with 'interested'\n"
        f"   b) Visit {_PRODUCT_URL}\n"
        "4. Keep tone peer-to-peer: short sentences, no jargon, no buzzwords.\n"
        "5. Make it feel like one recruiter talking to another.\n\n"
        "Return ONLY a JSON object with keys: pain_hypothesis, bandwidth_pressure, buyer_persona, "
        "outreach_angle, cold_email, linkedin_message, whatsapp_message, case_study_used.\n\n"
        f"Company: {lead.get('company_name')}\n"
        f"Industry: {lead.get('industry')}\n"
        f"Region: {lead.get('region')}\n"
        f"Total open jobs: {lead.get('total_open_jobs')}\n"
        f"Recruiter/TA jobs open: {lead.get('recruiter_jobs_open')}\n"
        f"TA coordinator/recruitment-ops jobs: {lead.get('ta_coordinator_jobs')}\n"
        f"High-volume roles open: {lead.get('high_volume_role_jobs')}\n"
        f"Urgent hiring: {lead.get('has_urgent_hiring')}\n"
        f"Multiple locations: {lead.get('has_multiple_locations')}\n"
        f"Decision maker: {lead.get('decision_maker_name')} ({lead.get('decision_maker_title')})\n"
        f"Detected signals: {signals}\n"
        f"Lead score: {lead.get('score')} ({lead.get('priority')} priority)\n"
        f"Matched case study bucket: {cs['label']} ({cs['headline']})\n"
    )


# ---------------------------------------------------------------------------
# Template fallback (deterministic — works without any API key)
# ---------------------------------------------------------------------------

def _template_output(lead: dict) -> dict:
    company = lead.get("company_name", "the company")
    dm = lead.get("decision_maker_name") or "there"
    dm_title = lead.get("decision_maker_title") or "Talent leader"
    open_jobs = lead.get("total_open_jobs", 0)
    recruiter_jobs = lead.get("recruiter_jobs_open", 0)
    region = lead.get("region") or "your region"

    cs = _get_case_study(lead)
    case_label = cs["label"]
    case_headline = cs["headline"]
    case_detail = cs["detail"]

    pain = (
        f"{company} is scaling fast — {open_jobs} open roles"
        + (f" and hiring {recruiter_jobs} recruiters/TA to keep up" if recruiter_jobs else "")
        + f". That's the exact pain RACHEL solves for {case_label.lower()}."
    )
    bandwidth = (
        f"With {recruiter_jobs or 'limited'} TA people juggling {open_jobs} reqs, "
        f"{company}'s team is probably underwater. RACHEL can lighten that load today."
    )
    persona = (
        f"Best buyer: {dm_title} at {company} — the person losing sleep over open seats."
    )
    angle = (
        f"Open with RACHEL's {case_label.lower()} win: {case_headline}. "
        f"Then ask if {company} wants the same outcome."
    )

    cold_email = (
        f"Subject: {company} + {open_jobs} open roles — quick win?\n\n"
        f"Hi {dm},\n\n"
        f"Noticed {company} is hiring across {open_jobs} roles"
        + (f" in {region}" if region else "")
        + ".\n\n"
        f"RACHEL is an AI recruitment tool built for {case_label.lower()}. "
        f"One client saw: {case_headline}.\n\n"
        f"Want to see if it fits {company}?\n\n"
        f"Reply 'interested' and I'll send a 3-min overview.\n"
        f"Or check it out directly: {_PRODUCT_URL}\n\n"
        f"Cheers,\n[Your name]"
    )

    linkedin = (
        f"Hi {dm}, saw {company} has {open_jobs} open reqs. "
        f"RACHEL helped a similar {case_label.lower()} shop: {case_headline}. "
        f"Want to see how? Reply 'interested' or grab a demo at {_PRODUCT_URL}"
    )

    whatsapp = (
        f"Hi {dm} — noticed {company} is scaling ({open_jobs} open roles). "
        f"RACHEL is AI recruitment automation. A {case_label.lower()} client hit: {case_headline}. "
        f"Interested? Reply here. Details: {_PRODUCT_URL}"
    )

    return {
        "pain_hypothesis": pain,
        "bandwidth_pressure": bandwidth,
        "buyer_persona": persona,
        "outreach_angle": angle,
        "cold_email": cold_email,
        "linkedin_message": linkedin,
        "whatsapp_message": whatsapp,
        "case_study_used": f"{case_label}: {case_headline}",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_outreach(lead: dict, api_key: str | None, base_url: str, model: str) -> dict:
    """Generate AI outreach drafts. Returns dict with AI_FIELDS keys."""
    if not api_key:
        logger.info("No OpenAI key configured; using template outreach for %s", lead.get("company_name"))
        return _template_output(lead)

    try:
        resp = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You output only valid JSON. "
                            "You are an SDR for RACHEL (AI recruitment automation). "
                            "Use peer tone: short, no jargon. Mention RACHEL by name. "
                            "Include dual CTAs: reply 'interested' and landing page link."
                        ),
                    },
                    {"role": "user", "content": _build_prompt(lead)},
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        fallback = _template_output(lead)
        return {field: data.get(field) or fallback[field] for field in AI_FIELDS}
    except Exception as exc:  # noqa: BLE001 - graceful fallback for any AI failure
        logger.warning("AI generation failed (%s); falling back to template", exc)
        return _template_output(lead)
