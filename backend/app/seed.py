"""Seed script: demo user, a sample campaign, and 10 dummy scored leads.

Idempotent — safe to run on every startup. Skips if the demo user already
has leads. Uses template AI output (no external API calls).
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.scoring import SignalInput, score_lead
from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Campaign, CompanyLead, JobPosting, ResearchRun, User
from app.services.classify import classify_title
from app.services.openai_service import _template_output
from app.services.sample_data import generate_companies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

DEMO_EMAIL = "demo@recloud.app"
DEMO_PASSWORD = "demo1234"


def seed() -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if not user:
            user = User(
                email=DEMO_EMAIL,
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name="Demo User",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Created demo user %s", DEMO_EMAIL)

        existing_leads = db.scalar(
            select(CompanyLead).where(CompanyLead.user_id == user.id).limit(1)
        )
        if existing_leads:
            logger.info("Seed leads already present; skipping")
            return

        campaign = Campaign(
            user_id=user.id,
            name="India Recruitment Pain Signals",
            industry="IT Services",
            region="India",
            min_employee_count=100,
            job_keywords=["software engineer", "support", "sales"],
            recruiter_keywords=["recruiter", "talent acquisition"],
            high_volume_role_keywords=["sales", "support", "bpo", "operations"],
            target_decision_maker_titles=["Head of Talent Acquisition", "VP People", "Director HR"],
            status="completed",
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        run = ResearchRun(
            campaign_id=campaign.id,
            user_id=user.id,
            status="completed",
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        db.add(run)
        db.commit()

        companies = generate_companies(campaign, count=10)
        created = 0
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
            ai = _template_output(
                {
                    "company_name": comp["company_name"],
                    "industry": comp["industry"],
                    "region": comp["region"],
                    "total_open_jobs": comp["total_open_jobs"],
                    "recruiter_jobs_open": comp["recruiter_jobs_open"],
                    "decision_maker_name": dm["name"] if dm else None,
                    "decision_maker_title": dm["title"] if dm else None,
                }
            )
            lead = CompanyLead(
                campaign_id=campaign.id,
                user_id=user.id,
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
                decision_maker_email=dm["email"] if dm else None,
                decision_maker_email_status="unknown" if dm else None,
                score=result.score,
                priority=result.priority,
                signals=result.as_signals(),
                ai_pain_hypothesis=ai["pain_hypothesis"],
                ai_bandwidth_pressure=ai["bandwidth_pressure"],
                ai_buyer_persona=ai["buyer_persona"],
                ai_outreach_angle=ai["outreach_angle"],
                ai_cold_email=ai["cold_email"],
                ai_linkedin_message=ai["linkedin_message"],
                ai_whatsapp_message=ai["whatsapp_message"],
                status="new",
            )
            db.add(lead)
            db.flush()
            for job in comp.get("sample_jobs", []):
                flags = classify_title(job["title"], {
                    "recruiter_keywords": campaign.recruiter_keywords,
                    "high_volume_role_keywords": campaign.high_volume_role_keywords,
                })
                db.add(
                    JobPosting(
                        company_lead_id=lead.id,
                        title=job["title"],
                        location=job.get("location"),
                        url=comp["careers_url"],
                        posted_date=job.get("posted_date"),
                        source="sample",
                        is_recruiter_role=flags["is_recruiter_role"],
                        is_ta_coordinator=flags["is_ta_coordinator"],
                        is_high_volume_role=flags["is_high_volume_role"],
                        is_urgent=job.get("urgent", False) or flags["is_urgent"],
                        is_stale=job.get("stale", False),
                    )
                )
            created += 1

        run.companies_found = len(companies)
        run.leads_created = created
        db.commit()
        logger.info("Seeded %s demo leads for campaign '%s'", created, campaign.name)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
