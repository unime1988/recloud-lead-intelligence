from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    settings: Mapped["IntegrationSetting | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    min_employee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    job_keywords: Mapped[list] = mapped_column(JSONB, default=list)
    recruiter_keywords: Mapped[list] = mapped_column(JSONB, default=list)
    high_volume_role_keywords: Mapped[list] = mapped_column(JSONB, default=list)
    target_decision_maker_titles: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="campaigns")
    leads: Mapped[list["CompanyLead"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
    research_runs: Mapped[list["ResearchRun"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class CompanyLead(Base):
    __tablename__ = "company_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    careers_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Hiring signals (raw counts / flags)
    total_open_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recruiter_jobs_open: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ta_coordinator_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_volume_role_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_urgent_hiring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_multiple_locations: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_stale_jobs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locations: Mapped[list] = mapped_column(JSONB, default=list)

    # Decision maker
    decision_maker_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_maker_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_maker_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_maker_email_status: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Scoring
    score: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="Low", index=True, nullable=False)
    signals: Mapped[list] = mapped_column(JSONB, default=list)

    # AI-generated output
    ai_pain_hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_bandwidth_pressure: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_buyer_persona: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_outreach_angle: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_cold_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_linkedin_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_whatsapp_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="leads")
    job_postings: Mapped[list["JobPosting"]] = relationship(
        back_populates="company_lead", cascade="all, delete-orphan"
    )


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_lead_id: Mapped[int] = mapped_column(
        ForeignKey("company_leads.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    posted_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_recruiter_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_ta_coordinator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_high_volume_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company_lead: Mapped["CompanyLead"] = relationship(back_populates="job_postings")


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True, nullable=False)
    companies_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leads_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    log: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    campaign: Mapped["Campaign"] = relationship(back_populates="research_runs")


class IntegrationSetting(Base):
    __tablename__ = "integration_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )

    openai_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    openai_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    openai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    firecrawl_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    jobspy_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hunter_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    zerobounce_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    apollo_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reacher_api_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    baserow_api_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    baserow_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    twenty_api_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    twenty_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hubspot_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    n8n_webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="settings")
