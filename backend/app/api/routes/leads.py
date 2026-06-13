import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Campaign, CompanyLead, User
from app.schemas import (
    CompanyLeadDetail,
    CompanyLeadOut,
    LeadListResponse,
    LeadStatusUpdate,
)

router = APIRouter(prefix="/api/leads", tags=["leads"])

SORTABLE = {
    "score": CompanyLead.score,
    "company_name": CompanyLead.company_name,
    "total_open_jobs": CompanyLead.total_open_jobs,
    "created_at": CompanyLead.created_at,
    "priority": CompanyLead.score,
}


@router.get("", response_model=LeadListResponse)
def list_leads(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    campaign_id: int | None = None,
    priority: str | None = None,
    search: str | None = None,
    min_score: int | None = None,
    has_decision_maker: bool | None = None,
    sort_by: str = Query("score"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> LeadListResponse:
    stmt = select(CompanyLead).where(CompanyLead.user_id == user.id)

    if campaign_id is not None:
        stmt = stmt.where(CompanyLead.campaign_id == campaign_id)
    if priority:
        stmt = stmt.where(CompanyLead.priority == priority)
    if min_score is not None:
        stmt = stmt.where(CompanyLead.score >= min_score)
    if has_decision_maker is True:
        stmt = stmt.where(CompanyLead.decision_maker_name.isnot(None))
    elif has_decision_maker is False:
        stmt = stmt.where(CompanyLead.decision_maker_name.is_(None))
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(CompanyLead.company_name).like(like),
                func.lower(CompanyLead.industry).like(like),
                func.lower(CompanyLead.region).like(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    column = SORTABLE.get(sort_by, CompanyLead.score)
    order = asc(column) if sort_dir == "asc" else desc(column)
    stmt = stmt.order_by(order, desc(CompanyLead.id))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    leads = db.scalars(stmt).all()
    pages = max(1, math.ceil(total / page_size))
    return LeadListResponse(
        items=[CompanyLeadOut.model_validate(lead) for lead in leads],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{lead_id}", response_model=CompanyLeadDetail)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CompanyLeadDetail:
    lead = db.scalar(
        select(CompanyLead)
        .where(CompanyLead.id == lead_id, CompanyLead.user_id == user.id)
        .options(selectinload(CompanyLead.job_postings))
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    detail = CompanyLeadDetail.model_validate(lead)
    campaign = db.get(Campaign, lead.campaign_id)
    detail.campaign_name = campaign.name if campaign else None
    return detail


@router.patch("/{lead_id}/status", response_model=CompanyLeadOut)
def update_lead_status(
    lead_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CompanyLeadOut:
    lead = db.scalar(
        select(CompanyLead).where(CompanyLead.id == lead_id, CompanyLead.user_id == user.id)
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = payload.status
    db.commit()
    db.refresh(lead)
    return CompanyLeadOut.model_validate(lead)
