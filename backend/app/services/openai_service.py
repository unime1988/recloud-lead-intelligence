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


# ---------------------------------------------------------------------------
# Rachel AI case studies — matched to lead size/type
# ---------------------------------------------------------------------------

_CASE_STUDIES = {
    "bpo_large": (
        "A Tier-1 BPO with 500+ open support roles was drowning in 6-day shortlist "
        "cycles. After deploying RACHEL, they delivered decision-ready shortlists in "
        "24 hours — same team, same budget. CQV visibility changed how they run hiring."
    ),
    "it_services": (
        "A global IT services firm spent 28 hrs/week on recruiter admin for engineering "
        "roles. RACHEL compressed their first-round cycle from days to hours — now at "
        "8 hrs/week, protecting senior engineering panel time."
    ),
    "staffing_agency": (
        "A mid-size staffing agency handling 200+ roles/month couldn't scale interviews "
        "fast enough. RACHEL now screens and interviews autonomously — they scaled 3x "
        "placements without hiring a single additional recruiter."
    ),
    "startup_growing": (
        "A fast-growing startup had 40 open roles and only 2 recruiters. Scheduling alone "
        "ate half their week. RACHEL's self-serve scheduling + AI first-rounds freed them "
        "up — they filled seats 70% faster without adding headcount."
    ),
    "enterprise_gcc": (
        "A Global Capability Center hiring across 4 countries needed consistent first-round "
        "rigor. RACHEL standardized structured interviews across time zones — delivering "
        "predictable shortlists and cutting cost-per-qualified-CV by 55%."
    ),
}

RACHEL_LINK = "https://recloudconsulting.com/relcoud-agentic-engine.php"


def _pick_case_study(lead: dict) -> str:
    """Select the most relevant case study based on lead characteristics."""
    company = (lead.get("company_name") or "").lower()
    industry = (lead.get("industry") or "").lower()
    open_jobs = lead.get("total_open_jobs", 0)

    # Staffing/recruitment agency
    if any(kw in company for kw in ("staffing", "recruitment", "manpower", "placement", "consulting", "agency")):
        return _CASE_STUDIES["staffing_agency"]
    if "recruitment" in industry or "staffing" in industry:
        return _CASE_STUDIES["staffing_agency"]

    # BPO / large volume
    if any(kw in company for kw in ("bpo", "ites", "outsourc", "call center")):
        return _CASE_STUDIES["bpo_large"]
    if open_jobs >= 50:
        return _CASE_STUDIES["bpo_large"]

    # IT services
    if any(kw in company for kw in ("tech", "software", "it service", "infosys", "wipro", "tcs")):
        return _CASE_STUDIES["it_services"]

    # Enterprise / GCC
    if open_jobs >= 20:
        return _CASE_STUDIES["enterprise_gcc"]

    # Default: startup/growing company
    return _CASE_STUDIES["startup_growing"]


def _build_prompt(lead: dict) -> str:
    signals = ", ".join(s.get("label", "") for s in lead.get("signals", [])) or "general hiring activity"
    case_study = _pick_case_study(lead)
    return (
        "You are writing cold outreach for RACHEL — an autonomous hiring engine by ReCloud. "
        "RACHEL screens CVs, runs structured AI first-round interviews (technical + non-technical), "
        "schedules candidates via self-serve calendars, and delivers decision-ready shortlists in 24 hours. "
        "It processes 1,00,000+ resumes, executes 8,000+ interviews, and has enabled 2,500+ offers. "
        "Key results: up to 55% lower cost-per-qualified-CV, 70% less recruiter effort, 24-hour shortlists.\n\n"
        #
        f"RACHEL LINK (include in email): {RACHEL_LINK}\n\n"
        #
        f"CASE STUDY TO USE (pick the proof point from this):\n{case_study}\n\n"
        #
        # --- Cold-email skill methodology ---
        #
        "WRITING RULES (follow strictly):\n"
        "- Write like a peer, not a vendor. Use contractions. If it sounds like \n"
        "  marketing copy, rewrite it. No jargon: no 'synergy', 'leverage', \n"
        "  'circle back', 'best-in-class', 'leading provider'.\n"
        "- Every sentence must earn its place. Under 90 words for the email body.\n"
        "- Lead with THEIR world, not yours. 'You/your' dominates over 'I/we'.\n"
        "- Do NOT open with 'I hope this email finds you well', 'My name is X', \n"
        "  or 'I came across your profile'. Never use 'leverage' or 'synergy'.\n"
        "- Mention RACHEL by name naturally (not in subject line).\n"
        "- Personalization must connect to the problem. The observation about their \n"
        "  hiring signals should naturally lead into why RACHEL matters to them.\n\n"
        #
        "SUBJECT LINE RULES:\n"
        "- 2-4 words, all lowercase, no punctuation tricks, no emojis.\n"
        "- Should look like it came from a colleague, not a vendor.\n"
        "- No product name in subject, no 'increase/boost/ROI', no prospect first name.\n"
        "- Examples: 'interview bandwidth', 'hiring bottleneck', 'screening capacity'.\n\n"
        #
        "FRAMEWORK — use Observation → Problem → Proof → Ask (PAS variant):\n"
        "1. Observation: reference a specific hiring signal connected to interview pain.\n"
        "2. Problem: what this usually means — bottleneck, scheduling chaos, inconsistency.\n"
        "3. Proof: one concrete result FROM the case study above. Be specific.\n"
        "4. Two CTAs:\n"
        "   a) Reply CTA: 'Just reply \"interested\" and I\'ll send details' or \n"
        "      'Reply \"hi\" and I\'ll share how' — keep it one word reply.\n"
        f"   b) Link CTA: 'Or see how it works: {RACHEL_LINK}' — natural, not pushy.\n\n"
        #
        "COLD EMAIL FORMAT (subject_line: ... then body: ...):\n"
        "- Include BOTH CTAs at the end — the reply-based one first, then the link.\n"
        "- Sign off casually: just a first name, no title.\n\n"
        #
        "LINKEDIN MESSAGE: 2-3 sentences max. Same peer tone. Include RACHEL link.\n"
        "WHATSAPP MESSAGE: 1-2 sentences. Ultra-brief. Curiosity-driven. Include link.\n\n"
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
    """Fallback templates following cold-email skill + Rachel AI specifics:
    - Peer voice, not vendor voice
    - 2-4 word lowercase subject line
    - Observation → Problem → Proof → Ask (PAS)
    - Under 90 words body, dual CTAs (reply + link)
    - RACHEL mentioned by name with case study proof
    """
    company = lead.get("company_name", "the company")
    dm = lead.get("decision_maker_name") or "there"
    dm_title = lead.get("decision_maker_title") or "Talent leader"
    open_jobs = lead.get("total_open_jobs", 0)
    recruiter_jobs = lead.get("recruiter_jobs_open", 0)
    case_study = _pick_case_study(lead)

    pain = (
        f"{company} has {open_jobs} open roles"
        + (f" and is hiring {recruiter_jobs} recruiters" if recruiter_jobs else "")
        + " — that's a lot of interviews competing for limited bandwidth. "
        "At this volume, first-round screening and scheduling alone can consume "
        "the entire TA team's week."
    )
    bandwidth = (
        f"Every role needs multiple interview rounds. At {open_jobs} openings, "
        f"{company}'s interviewers are likely the bottleneck, not the pipeline. "
        f"RACHEL automates the entire first-round — screening, scheduling, and "
        f"structured interviews — delivering shortlists in 24 hours."
    )
    persona = f"{dm_title} or Head of TA at {company} — owns the interview throughput problem."
    angle = (
        f"Observation: {open_jobs} open roles = heavy interview load. "
        f"Problem: manual screening + scheduling = bottleneck. "
        f"Proof: {case_study[:80]}... "
        f"Ask: dual CTA — reply 'interested' or visit RACHEL link."
    )

    # --- Cold email: PAS framework, peer voice, RACHEL by name, dual CTAs ---
    cold_email = (
        f"subject_line: interview bandwidth\n\n"
        f"body: Hi {dm},\n\n"
        f"{company}'s got {open_jobs} roles open"
        + (f" and you're hiring more recruiters" if recruiter_jobs else "")
        + " — that usually means interviews are the bottleneck, not sourcing.\n\n"
        f"A similar-sized team was stuck in the same loop. They plugged in RACHEL "
        f"(an autonomous first-round engine) and went from 6-day shortlists to 24 hours "
        f"— 70% less recruiter effort, same team, same budget.\n\n"
        f"If that sounds relevant, just reply \"interested\" and I'll share how it'd "
        f"work for {company}.\n\n"
        f"Or take a quick look here: {RACHEL_LINK}\n\n"
        f"Cheers"
    )

    # --- LinkedIn: 2-3 sentences, peer tone, include link ---
    linkedin = (
        f"Hi {dm} — {open_jobs} open roles at {company} means a heavy interview load. "
        f"RACHEL runs structured first-rounds autonomously and delivers shortlists in 24 hrs. "
        f"Worth a look? {RACHEL_LINK}"
    )

    # --- WhatsApp: 1-2 sentences, ultra-brief, curiosity + link ---
    whatsapp = (
        f"Hi {dm} — {company} is hiring at scale. What if first-round interviews "
        f"ran on autopilot? Quick look: {RACHEL_LINK}"
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
