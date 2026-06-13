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
        "You are an expert cold email writer for Rachel AI — an AI-powered interview "
        "platform that conducts technical and non-technical interviews autonomously. "
        "Rachel AI processes 1,000 interviews simultaneously, works 24/7/365, and "
        "helps companies scale hiring 10x without adding recruiters.\n\n"
        #
        # --- Cold-email skill methodology ---
        #
        "WRITING RULES (follow strictly):\n"
        "- Write like a peer, not a vendor. Use contractions. If it sounds like \n"
        "  marketing copy, rewrite it. No jargon: no 'synergy', 'leverage', \n"
        "  'circle back', 'best-in-class', 'leading provider'.\n"
        "- Every sentence must earn its place. Under 75 words for the email body.\n"
        "- Lead with THEIR world, not yours. 'You/your' dominates over 'I/we'.\n"
        "- Do NOT open with 'I hope this email finds you well', 'My name is X', \n"
        "  or 'I came across your profile'. Never use 'leverage' or 'synergy'.\n"
        "- One ask, low friction. Use interest-based CTAs like 'Worth exploring?' \n"
        "  or 'Would this be useful?' — NOT 'Book a 30-min call'.\n"
        "- Personalization must connect to the problem. The observation about their \n"
        "  hiring signals should naturally lead into why Rachel AI matters to them.\n\n"
        #
        "SUBJECT LINE RULES:\n"
        "- 2-4 words, all lowercase, no punctuation tricks, no emojis.\n"
        "- Should look like it came from a colleague, not a vendor.\n"
        "- No product name, no 'increase/boost/ROI', no prospect first name.\n"
        "- Examples of good subject lines: 'interview bandwidth', 'hiring bottleneck', \n"
        "  'screening capacity', 'candidate pipeline'.\n\n"
        #
        "FRAMEWORK — use Observation → Problem → Proof → Ask (PAS variant):\n"
        "1. Observation: reference a specific hiring signal (e.g. their open roles, \n"
        "   recruiter postings, urgent hiring) connected to the interview problem.\n"
        "2. Problem: what this usually means — interview bottleneck, scheduling chaos, \n"
        "   inconsistent assessments, interviewer fatigue.\n"
        "3. Proof: one concrete result — e.g. 'cut time-to-hire by 70%' or \n"
        "   'screened 5,000 candidates in a week without adding headcount'.\n"
        "4. Ask: low-friction CTA — 'Worth a look?' / 'Relevant to you?'\n\n"
        #
        "LINKEDIN MESSAGE: 2-3 sentences max. Same peer tone. No pitch deck compression.\n"
        "WHATSAPP MESSAGE: 1-2 sentences. Ultra-brief. Curiosity-driven.\n\n"
        #
        "Return ONLY a JSON object with keys: pain_hypothesis, bandwidth_pressure, \n"
        "buyer_persona, outreach_angle, cold_email, linkedin_message, whatsapp_message.\n\n"
        #
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
    """Fallback templates following cold-email skill principles:
    - Peer voice, not vendor voice
    - 2-4 word lowercase subject line
    - Observation → Problem → Proof → Ask (PAS)
    - Under 75 words body, interest-based CTA
    """
    company = lead.get("company_name", "the company")
    dm = lead.get("decision_maker_name") or "there"
    dm_title = lead.get("decision_maker_title") or "Talent leader"
    open_jobs = lead.get("total_open_jobs", 0)
    recruiter_jobs = lead.get("recruiter_jobs_open", 0)

    pain = (
        f"{company} has {open_jobs} open roles"
        + (f" and is hiring {recruiter_jobs} recruiters" if recruiter_jobs else "")
        + " — that's a lot of interviews competing for limited bandwidth."
    )
    bandwidth = (
        f"Every role needs multiple interview rounds. At {open_jobs} openings, "
        f"{company}'s interviewers are likely the bottleneck, not the pipeline."
    )
    persona = f"{dm_title} or Head of TA at {company} — owns the interview throughput problem."
    angle = (
        f"Observation: {open_jobs} open roles = thousands of interviews/month. "
        f"Problem: interviewer bandwidth caps hiring speed. "
        f"Proof: Rachel AI screens 1,000 candidates simultaneously, 24/7. "
        f"Ask: worth exploring?"
    )

    # --- Cold email: PAS framework, peer voice, lowercase 2-4 word subject ---
    cold_email = (
        f"Subject: interview bandwidth\n\n"
        f"Hi {dm},\n\n"
        f"{company}'s got {open_jobs} roles open"
        + (f" and you're hiring more recruiters" if recruiter_jobs else "")
        + " — that usually means interviews are the bottleneck, not sourcing.\n\n"
        f"One company in a similar spot started running interviews autonomously "
        f"and cut time-to-hire by 70% without adding headcount.\n\n"
        f"Relevant to you?\n\n"
        f"Best,\n[Your name]"
    )

    # --- LinkedIn: 2-3 sentences, peer tone ---
    linkedin = (
        f"Hi {dm} — {open_jobs} open roles at {company} means a lot of interviews. "
        f"Curious if you've looked at running them autonomously? "
        f"Happy to share what's working for similar teams."
    )

    # --- WhatsApp: 1-2 sentences, ultra-brief ---
    whatsapp = (
        f"Hi {dm} — noticed {company} is hiring at scale. "
        f"Quick question: is interview bandwidth a bottleneck for you right now?"
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


def _stringify(value: object) -> str:
    """Convert a value to a plain string for DB storage.

    OpenAI may return structured objects (e.g. cold_email as
    ``{"subject": "...", "body": "..."}``). Flatten them to text.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "subject" in value and "body" in value:
            return f"Subject: {value['subject']}\n\n{value['body']}"
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)


def _ensure_strings(result: dict) -> dict:
    """Ensure every AI field value is a plain string."""
    return {k: _stringify(v) for k, v in result.items()}


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
        result = {field: data.get(field) or _template_output(lead)[field] for field in AI_FIELDS}
        return _ensure_strings(result)
    except Exception as exc:  # noqa: BLE001 - graceful fallback for any AI failure
        logger.warning("AI generation failed (%s); falling back to template", exc)
        return _template_output(lead)
