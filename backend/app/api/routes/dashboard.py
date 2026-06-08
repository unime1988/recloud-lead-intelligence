from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Campaign, CompanyLead, User
from app.schemas import CompanyLeadOut, DashboardStats, PriorityCount

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

PRIORITY_ORDER = ["Very Hot", "High", "Medium", "Low"]


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> DashboardStats:
    total_campaigns = db.scalar(
        select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
    ) or 0
    total_leads = db.scalar(
        select(func.count(CompanyLead.id)).where(CompanyLead.user_id == user.id)
    ) or 0
    avg_score = db.scalar(
        select(func.coalesce(func.avg(CompanyLead.score), 0.0)).where(CompanyLead.user_id == user.id)
    ) or 0.0
    total_open_jobs = db.scalar(
        select(func.coalesce(func.sum(CompanyLead.total_open_jobs), 0)).where(
            CompanyLead.user_id == user.id
        )
    ) or 0
    leads_with_dm = db.scalar(
        select(func.count(CompanyLead.id)).where(
            CompanyLead.user_id == user.id, CompanyLead.decision_maker_name.isnot(None)
        )
    ) or 0

    rows = db.execute(
        select(CompanyLead.priority, func.count(CompanyLead.id))
        .where(CompanyLead.user_id == user.id)
        .group_by(CompanyLead.priority)
    ).all()
    counts = {priority: count for priority, count in rows}
    priority_breakdown = [
        PriorityCount(priority=p, count=counts.get(p, 0)) for p in PRIORITY_ORDER
    ]

    top_leads = db.scalars(
        select(CompanyLead)
        .where(CompanyLead.user_id == user.id)
        .order_by(CompanyLead.score.desc(), CompanyLead.id.desc())
        .limit(5)
    ).all()

    return DashboardStats(
        total_campaigns=total_campaigns,
        total_leads=total_leads,
        avg_score=round(float(avg_score), 1),
        priority_breakdown=priority_breakdown,
        top_leads=[CompanyLeadOut.model_validate(lead) for lead in top_leads],
        leads_with_decision_maker=leads_with_dm,
        total_open_jobs=int(total_open_jobs),
    )
