from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Campaign, CompanyLead, ResearchRun, User
from app.schemas import (
    CampaignCreate,
    CampaignOut,
    CampaignUpdate,
    ResearchRunOut,
)
from app.services.research import enqueue_research_run

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def _to_out(db: Session, campaign: Campaign) -> CampaignOut:
    leads_count = db.scalar(
        select(func.count(CompanyLead.id)).where(CompanyLead.campaign_id == campaign.id)
    )
    data = CampaignOut.model_validate(campaign)
    data.leads_count = leads_count or 0
    return data


def _get_owned_campaign(db: Session, campaign_id: int, user: User) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if not campaign or campaign.user_id != user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("", response_model=list[CampaignOut])
def list_campaigns(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[CampaignOut]:
    campaigns = db.scalars(
        select(Campaign).where(Campaign.user_id == user.id).order_by(Campaign.created_at.desc())
    ).all()
    return [_to_out(db, c) for c in campaigns]


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CampaignOut:
    campaign = Campaign(user_id=user.id, **payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return _to_out(db, campaign)


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CampaignOut:
    campaign = _get_owned_campaign(db, campaign_id, user)
    return _to_out(db, campaign)


@router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CampaignOut:
    campaign = _get_owned_campaign(db, campaign_id, user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)
    db.commit()
    db.refresh(campaign)
    return _to_out(db, campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    campaign = _get_owned_campaign(db, campaign_id, user)
    db.delete(campaign)
    db.commit()


@router.post("/{campaign_id}/research", response_model=ResearchRunOut, status_code=status.HTTP_202_ACCEPTED)
def start_research(
    campaign_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResearchRunOut:
    campaign = _get_owned_campaign(db, campaign_id, user)
    run = ResearchRun(campaign_id=campaign.id, user_id=user.id, status="queued")
    campaign.status = "researching"
    db.add(run)
    db.commit()
    db.refresh(run)
    enqueue_research_run(run.id)
    return ResearchRunOut.model_validate(run)


@router.get("/{campaign_id}/runs", response_model=list[ResearchRunOut])
def list_runs(
    campaign_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ResearchRunOut]:
    _get_owned_campaign(db, campaign_id, user)
    runs = db.scalars(
        select(ResearchRun)
        .where(ResearchRun.campaign_id == campaign_id)
        .order_by(ResearchRun.created_at.desc())
    ).all()
    return [ResearchRunOut.model_validate(r) for r in runs]
