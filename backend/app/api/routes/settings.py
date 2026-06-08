from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings as app_settings
from app.database import get_db
from app.models import IntegrationSetting, User
from app.schemas import IntegrationSettingOut, IntegrationSettingUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create(db: Session, user: User) -> IntegrationSetting:
    row = db.scalar(select(IntegrationSetting).where(IntegrationSetting.user_id == user.id))
    if not row:
        row = IntegrationSetting(
            user_id=user.id,
            openai_base_url=app_settings.openai_base_url,
            openai_model=app_settings.openai_model,
            jobspy_enabled=app_settings.jobspy_enabled,
            reacher_api_url=app_settings.reacher_api_url,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _to_out(row: IntegrationSetting) -> IntegrationSettingOut:
    return IntegrationSettingOut(
        openai_api_key_set=bool(row.openai_api_key),
        openai_base_url=row.openai_base_url,
        openai_model=row.openai_model,
        firecrawl_api_key_set=bool(row.firecrawl_api_key),
        jobspy_enabled=row.jobspy_enabled,
        hunter_api_key_set=bool(row.hunter_api_key),
        zerobounce_api_key_set=bool(row.zerobounce_api_key),
        apollo_api_key_set=bool(row.apollo_api_key),
        reacher_api_url=row.reacher_api_url,
        baserow_api_url=row.baserow_api_url,
        baserow_api_key_set=bool(row.baserow_api_key),
        twenty_api_url=row.twenty_api_url,
        twenty_api_key_set=bool(row.twenty_api_key),
        hubspot_api_key_set=bool(row.hubspot_api_key),
        n8n_webhook_url=row.n8n_webhook_url,
    )


@router.get("", response_model=IntegrationSettingOut)
def get_settings(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> IntegrationSettingOut:
    return _to_out(_get_or_create(db, user))


@router.put("", response_model=IntegrationSettingOut)
def update_settings(
    payload: IntegrationSettingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IntegrationSettingOut:
    row = _get_or_create(db, user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        # Skip empty-string secret overwrites so users don't clobber stored keys by accident.
        if value == "":
            continue
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return _to_out(row)
