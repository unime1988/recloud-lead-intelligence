from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str | None = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Campaigns ----------
class CampaignBase(BaseModel):
    name: str
    industry: str | None = None
    region: str | None = None
    min_employee_count: int = 0
    job_keywords: list[str] = []
    recruiter_keywords: list[str] = []
    high_volume_role_keywords: list[str] = []
    target_decision_maker_titles: list[str] = []


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    region: str | None = None
    min_employee_count: int | None = None
    job_keywords: list[str] | None = None
    recruiter_keywords: list[str] | None = None
    high_volume_role_keywords: list[str] | None = None
    target_decision_maker_titles: list[str] | None = None
    status: str | None = None


class CampaignOut(CampaignBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    leads_count: int = 0


# ---------- Jobs ----------
class JobPostingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    location: str | None = None
    url: str | None = None
    posted_date: str | None = None
    source: str | None = None
    is_recruiter_role: bool
    is_ta_coordinator: bool
    is_high_volume_role: bool
    is_urgent: bool
    is_stale: bool


# ---------- Leads ----------
class SignalItem(BaseModel):
    label: str
    points: int


class CompanyLeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    campaign_id: int
    company_name: str
    website: str | None = None
    careers_url: str | None = None
    industry: str | None = None
    region: str | None = None
    employee_count: int | None = None
    total_open_jobs: int
    recruiter_jobs_open: int
    ta_coordinator_jobs: int
    high_volume_role_jobs: int
    has_urgent_hiring: bool
    has_multiple_locations: bool
    has_stale_jobs: bool
    locations: list = []
    decision_maker_name: str | None = None
    decision_maker_title: str | None = None
    decision_maker_email: str | None = None
    decision_maker_email_status: str | None = None
    score: int
    priority: str
    signals: list = []
    status: str
    created_at: datetime
    updated_at: datetime


class CompanyLeadDetail(CompanyLeadOut):
    ai_pain_hypothesis: str | None = None
    ai_bandwidth_pressure: str | None = None
    ai_buyer_persona: str | None = None
    ai_outreach_angle: str | None = None
    ai_case_study_used: str | None = None
    ai_cold_email: str | None = None
    ai_linkedin_message: str | None = None
    ai_whatsapp_message: str | None = None
    job_postings: list[JobPostingOut] = []
    campaign_name: str | None = None


class LeadListResponse(BaseModel):
    items: list[CompanyLeadOut]
    total: int
    page: int
    page_size: int
    pages: int


class LeadStatusUpdate(BaseModel):
    status: str


# ---------- Research runs ----------
class ResearchRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    campaign_id: int
    status: str
    companies_found: int
    leads_created: int
    error: str | None = None
    log: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


# ---------- Dashboard ----------
class PriorityCount(BaseModel):
    priority: str
    count: int


class DashboardStats(BaseModel):
    total_campaigns: int
    total_leads: int
    avg_score: float
    priority_breakdown: list[PriorityCount]
    top_leads: list[CompanyLeadOut]
    leads_with_decision_maker: int
    total_open_jobs: int


# ---------- Settings ----------
class IntegrationSettingUpdate(BaseModel):
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None
    firecrawl_api_key: str | None = None
    jobspy_enabled: bool | None = None
    hunter_api_key: str | None = None
    zerobounce_api_key: str | None = None
    apollo_api_key: str | None = None
    reacher_api_url: str | None = None
    baserow_api_url: str | None = None
    baserow_api_key: str | None = None
    twenty_api_url: str | None = None
    twenty_api_key: str | None = None
    hubspot_api_key: str | None = None
    n8n_webhook_url: str | None = None


class IntegrationSettingOut(BaseModel):
    """API keys are masked; booleans/urls returned as-is."""
    openai_api_key_set: bool = False
    openai_base_url: str | None = None
    openai_model: str | None = None
    firecrawl_api_key_set: bool = False
    jobspy_enabled: bool = True
    hunter_api_key_set: bool = False
    zerobounce_api_key_set: bool = False
    apollo_api_key_set: bool = False
    reacher_api_url: str | None = None
    baserow_api_url: str | None = None
    baserow_api_key_set: bool = False
    twenty_api_url: str | None = None
    twenty_api_key_set: bool = False
    hubspot_api_key_set: bool = False
    n8n_webhook_url: str | None = None
