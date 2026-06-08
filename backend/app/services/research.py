"""Research run orchestration: build leads, score them, generate AI drafts."""

import logging
from datetime import datetime, timezone

from redis import Redis
from rq import Queue
from sqlalchemy import select

from app.config import settings
from app.core.scoring import SignalInput, score_lead
from app.database import SessionLocal
from app.models import Campaign, CompanyLead, IntegrationSetting, JobPosting, ResearchRun
from app.services import crm
from app.services.classify import classify_title
from app.services.email_verify import verify_email
from app.services.openai_service import generate_outreach
from app.services.sample_data import generate_companies

logger = logging.getLogger(__name__)


def enqueue_research_run(run_id: int) -> None:
    """Push a research job to the Redis queue; run inline if Redis is down."""
    try:
        conn = Redis.from_url(settings.redis_url)
        conn.ping()
        queue = Queue("research", connection=conn)
        queue.enqueue("app.services.research.run_research", run_id, job_timeout=900)
        logger.info("Enqueued research run %s", run_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not enqueue (%s); running inline", exc)
        run_research(run_id)


def _effective_settings(user_settings: IntegrationSetting | None) -> dict:
    """Merge per-user integration settings over app defaults."""
    def pick(attr: str, default):
        val = getattr(user_settings, attr, None) if user_settings else None
        return val if val not in (None, "") else default

    return {
        "openai_api_key": pick("openai_api_key", _clean(settings.openai_api_key)),
        "openai_base_url": pick("openai_base_url", settings.openai_base_url),
        "openai_model": pick("openai_model", settings.openai_model),
        "firecrawl_api_key": pick("firecrawl_api_key", _clean(settings.firecrawl_api_key)),
        "reacher_api_url": pick("reacher_api_url", _clean(settings.reacher_api_url)),
        "zerobounce_api_key": pick("zerobounce_api_key", _clean(settings.zerobounce_api_key)),
        "hunter_api_key": pick("hunter_api_key", _clean(settings.hunter_api_key)),
        "n8n_webhook_url": pick("n8n_webhook_url", _clean(settings.n8n_webhook_url)),
    }


def _clean(value: str | None) -> str:
    """Treat placeholder env values as unset."""
    if not value or str(value).startswith(("replace_with", "replace_if")):
        return ""
    return value


def run_research(run_id: int) -> None:
    db = SessionLocal()
    log_lines: list[str] = []
    try:
        run = db.get(ResearchRun, run_id)
        if not run:
            logger.warning("Research run %s not found", run_id)
            return
        campaign = db.get(Campaign, run.campaign_id)
        if not campaign:
            run.status = "failed"
            run.error = "Campaign not found"
            db.commit()
            return

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        user_settings = db.scalar(
            select(IntegrationSetting).where(IntegrationSetting.user_id == run.user_id)
        )
        eff = _effective_settings(user_settings)

        log_lines.append("Building company candidates from public job signals (sample fallback).")
        companies = generate_companies(campaign, count=settings.jobspy_default_results_limit and 10 or 10)
        run.companies_found = len(companies)

        leads_created = 0
        for comp in companies:
            dm = comp.get("decision_maker")
            signal = SignalInput(
                total_open_jobs=comp["total_open_jobs"],
                recruiter_jobs_open=comp["recruiter_jobs_open"],
                ta_coordinator_jobs=comp["ta_coordinator_jobs"],
                high_volume_role_jobs=comp["high_volume_role_jobs"],
                has_urgent_hiring=comp["has_urgent_hiring"],
                has_multiple_locations=comp["has_multiple_locations"],
                decision_maker_found=dm is not None,
            )
            result = score_lead(signal)

            dm_email = dm["email"] if dm else None
            dm_email_status = None
            if dm_email and settings.enable_email_verification:
                dm_email_status = verify_email(
                    dm_email,
                    reacher_url=eff["reacher_api_url"],
                    zerobounce_key=eff["zerobounce_api_key"],
                    hunter_key=eff["hunter_api_key"],
                )

            lead = CompanyLead(
                campaign_id=campaign.id,
                user_id=run.user_id,
                company_name=comp["company_name"],
                website=comp["website"],
                careers_url=comp["careers_url"],
                industry=comp["industry"],
                region=comp["region"],
                employee_count=comp["employee_count"],
                total_open_jobs=comp["total_open_jobs"],
                recruiter_jobs_open=comp["recruiter_jobs_open"],
                ta_coordinator_jobs=comp["ta_coordinator_jobs"],
                high_volume_role_jobs=comp["high_volume_role_jobs"],
                has_urgent_hiring=comp["has_urgent_hiring"],
                has_multiple_locations=comp["has_multiple_locations"],
                has_stale_jobs=comp["has_stale_jobs"],
                locations=comp["locations"],
                decision_maker_name=dm["name"] if dm else None,
                decision_maker_title=dm["title"] if dm else None,
                decision_maker_email=dm_email,
                decision_maker_email_status=dm_email_status,
                score=result.score,
                priority=result.priority,
                signals=result.as_signals(),
                status="new",
            )

            if settings.enable_ai_outreach_generation:
                ai = generate_outreach(
                    {
                        "company_name": comp["company_name"],
                        "industry": comp["industry"],
                        "region": comp["region"],
                        "total_open_jobs": comp["total_open_jobs"],
                        "recruiter_jobs_open": comp["recruiter_jobs_open"],
                        "ta_coordinator_jobs": comp["ta_coordinator_jobs"],
                        "high_volume_role_jobs": comp["high_volume_role_jobs"],
                        "has_urgent_hiring": comp["has_urgent_hiring"],
                        "has_multiple_locations": comp["has_multiple_locations"],
                        "decision_maker_name": dm["name"] if dm else None,
                        "decision_maker_title": dm["title"] if dm else None,
                        "score": result.score,
                        "priority": result.priority,
                        "signals": result.as_signals(),
                    },
                    api_key=eff["openai_api_key"],
                    base_url=eff["openai_base_url"],
                    model=eff["openai_model"],
                )
                lead.ai_pain_hypothesis = ai["pain_hypothesis"]
                lead.ai_bandwidth_pressure = ai["bandwidth_pressure"]
                lead.ai_buyer_persona = ai["buyer_persona"]
                lead.ai_outreach_angle = ai["outreach_angle"]
                lead.ai_cold_email = ai["cold_email"]
                lead.ai_linkedin_message = ai["linkedin_message"]
                lead.ai_whatsapp_message = ai["whatsapp_message"]

            db.add(lead)
            db.flush()  # get lead.id for job postings

            for job in comp.get("sample_jobs", []):
                flags = classify_title(job["title"], {
                    "recruiter_keywords": campaign.recruiter_keywords or [],
                    "high_volume_role_keywords": campaign.high_volume_role_keywords or [],
                })
                db.add(
                    JobPosting(
                        company_lead_id=lead.id,
                        title=job["title"],
                        location=job.get("location"),
                        url=comp["careers_url"],
                        posted_date=job.get("posted_date"),
                        source=comp.get("source", "sample"),
                        is_recruiter_role=flags["is_recruiter_role"],
                        is_ta_coordinator=flags["is_ta_coordinator"],
                        is_high_volume_role=flags["is_high_volume_role"],
                        is_urgent=job.get("urgent", False) or flags["is_urgent"],
                        is_stale=job.get("stale", False),
                    )
                )

            # Optional, non-default webhook export of the draft (never auto-sends outreach).
            if settings.enable_crm_sync and eff["n8n_webhook_url"]:
                crm.push_webhook(eff["n8n_webhook_url"], {"company": comp["company_name"], "score": result.score})

            leads_created += 1

        run.leads_created = leads_created
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        log_lines.append(f"Created {leads_created} scored leads.")
        run.log = "\n".join(log_lines)

        campaign.status = "completed"
        db.commit()
        logger.info("Research run %s completed: %s leads", run_id, leads_created)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Research run %s failed", run_id)
        db.rollback()
        run = db.get(ResearchRun, run_id)
        if run:
            run.status = "failed"
            run.error = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            run.log = "\n".join(log_lines)
            db.commit()
    finally:
        db.close()
