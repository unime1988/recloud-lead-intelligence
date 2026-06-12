"""OpenAI-compatible AI generation for outreach drafts.

Falls back to deterministic templates when no API key is configured so the
app produces useful drafts out of the box. Outreach is generated as DRAFTS
only; nothing is auto-sent.
"""

import json
import logging

import httpx

logger = logging.getLogger(__name__)

AI_FIELDS = [
    "pain_hypothesis",
    "bandwidth_pressure",
    "buyer_persona",
    "outreach_angle",
    "cold_email",
    "linkedin_message",
    "whatsapp_message",
]


def _build_prompt(lead: dict) -> str:
    signals = ", ".join(s.get("label", "") for s in lead.get("signals", [])) or "general hiring activity"
    return (
        "You are an SDR assistant for Rachel AI — an AI-powered interview platform "
        "that conducts technical and non-technical interviews autonomously. "
        "Rachel AI can process 1,000 interviews simultaneously, works 24/7/365, "
        "and helps companies scale hiring 10x without adding recruiters.\n\n"
        "Given the company hiring signals below, produce concise, non-pushy outreach DRAFTS "
        "that pitch Rachel AI as the solution to their interview bottleneck. "
        "Focus on: reducing time-to-hire, eliminating interviewer bandwidth constraints, "
        "consistent candidate assessments, and scaling without extra headcount.\n\n"
        "Return ONLY a JSON object with keys: pain_hypothesis, bandwidth_pressure, buyer_persona, "
        "outreach_angle, cold_email, linkedin_message, whatsapp_message.\n\n"
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
    )


def _template_output(lead: dict) -> dict:
    company = lead.get("company_name", "the company")
    dm = lead.get("decision_maker_name") or "there"
    dm_title = lead.get("decision_maker_title") or "Talent leader"
    open_jobs = lead.get("total_open_jobs", 0)
    recruiter_jobs = lead.get("recruiter_jobs_open", 0)
    region = lead.get("region") or "your region"

    pain = (
        f"{company} appears to be scaling hiring with {open_jobs} open roles"
        + (f" and {recruiter_jobs} recruiter/TA openings" if recruiter_jobs else "")
        + ". At this volume, interview scheduling and candidate screening become major bottlenecks."
    )
    bandwidth = (
        f"With {open_jobs} open positions, {company}'s interview pipeline is likely strained. "
        f"Each role requires multiple interview rounds — that's thousands of interviews "
        f"competing for limited interviewer time."
    )
    persona = f"Best buyer persona: {dm_title} or Head of Talent Acquisition at {company}."
    angle = (
        f"Rachel AI can handle 1,000 interviews simultaneously, 24/7 — letting {company} "
        f"screen candidates for all {open_jobs} roles without adding headcount."
    )
    cold_email = (
        f"Subject: {company} — automate interviews for {open_jobs} open roles\n\n"
        f"Hi {dm},\n\n"
        f"I noticed {company} is hiring across {open_jobs} roles"
        + (f" in {region}" if region else "")
        + ". At this scale, interview scheduling and screening become a real bottleneck.\n\n"
        f"Rachel AI conducts technical and non-technical interviews autonomously — "
        f"1,000 interviews at a time, 24/7. Companies using Rachel have cut time-to-hire by 70% "
        f"and scaled hiring 10x without adding recruiters.\n\n"
        f"Would a quick 15-min demo make sense this week?\n\n"
        f"Best,\n[Your name]"
    )
    linkedin = (
        f"Hi {dm}, saw {company} is hiring across {open_jobs} roles. "
        f"Rachel AI automates interviews (technical + non-technical) — 1,000 at a time, 24/7. "
        f"Companies using it have scaled hiring 10x. Worth a quick chat?"
    )
    whatsapp = (
        f"Hi {dm}, noticed {company} is scaling hiring ({open_jobs} open roles). "
        f"Rachel AI handles interviews 24/7 — 1,000 simultaneously. "
        f"Could I share a 2-min overview?"
    )
    return {
        "pain_hypothesis": pain,
        "bandwidth_pressure": bandwidth,
        "buyer_persona": persona,
        "outreach_angle": angle,
        "cold_email": cold_email,
        "linkedin_message": linkedin,
        "whatsapp_message": whatsapp,
    }


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
                    {"role": "system", "content": "You output only valid JSON."},
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
        return {field: data.get(field) or _template_output(lead)[field] for field in AI_FIELDS}
    except Exception as exc:  # noqa: BLE001 - graceful fallback for any AI failure
        logger.warning("AI generation failed (%s); falling back to template", exc)
        return _template_output(lead)
