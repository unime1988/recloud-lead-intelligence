import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings as app_settings
from app.database import get_db
from app.models import CompanyLead, User

router = APIRouter(prefix="/api/export", tags=["export"])

CSV_COLUMNS = [
    "company_name",
    "website",
    "careers_url",
    "industry",
    "region",
    "employee_count",
    "total_open_jobs",
    "recruiter_jobs_open",
    "ta_coordinator_jobs",
    "high_volume_role_jobs",
    "has_urgent_hiring",
    "has_multiple_locations",
    "decision_maker_name",
    "decision_maker_title",
    "decision_maker_email",
    "decision_maker_email_status",
    "score",
    "priority",
    "status",
]


@router.get("/leads.csv")
def export_leads_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    campaign_id: int | None = None,
    priority: str | None = None,
    search: str | None = None,
) -> StreamingResponse:
    if not app_settings.enable_csv_export:
        raise HTTPException(status_code=403, detail="CSV export is disabled")

    stmt = select(CompanyLead).where(CompanyLead.user_id == user.id)
    if campaign_id is not None:
        stmt = stmt.where(CompanyLead.campaign_id == campaign_id)
    if priority:
        stmt = stmt.where(CompanyLead.priority == priority)
    if search:
        like = f"%{search.lower()}%"
        from sqlalchemy import func

        stmt = stmt.where(
            or_(
                func.lower(CompanyLead.company_name).like(like),
                func.lower(CompanyLead.industry).like(like),
            )
        )
    stmt = stmt.order_by(CompanyLead.score.desc())
    leads = db.scalars(stmt).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for lead in leads:
        writer.writerow([getattr(lead, col) for col in CSV_COLUMNS])
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=recloud_leads.csv"},
    )
