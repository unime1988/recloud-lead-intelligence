export interface User {
  id: number;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface Campaign {
  id: number;
  name: string;
  industry: string | null;
  region: string | null;
  min_employee_count: number;
  company_type: string;
  job_keywords: string[];
  recruiter_keywords: string[];
  high_volume_role_keywords: string[];
  target_decision_maker_titles: string[];
  status: string;
  created_at: string;
  updated_at: string;
  leads_count: number;
}

export interface SignalItem {
  label: string;
  points: number;
}

export interface Lead {
  id: number;
  campaign_id: number;
  company_name: string;
  website: string | null;
  careers_url: string | null;
  industry: string | null;
  region: string | null;
  employee_count: number | null;
  total_open_jobs: number;
  recruiter_jobs_open: number;
  ta_coordinator_jobs: number;
  high_volume_role_jobs: number;
  has_urgent_hiring: boolean;
  has_multiple_locations: boolean;
  has_stale_jobs: boolean;
  locations: string[];
  decision_maker_name: string | null;
  decision_maker_title: string | null;
  decision_maker_email: string | null;
  decision_maker_email_status: string | null;
  score: number;
  priority: string;
  signals: SignalItem[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface JobPosting {
  id: number;
  title: string;
  location: string | null;
  url: string | null;
  posted_date: string | null;
  source: string | null;
  is_recruiter_role: boolean;
  is_ta_coordinator: boolean;
  is_high_volume_role: boolean;
  is_urgent: boolean;
  is_stale: boolean;
}

export interface LeadDetail extends Lead {
  ai_pain_hypothesis: string | null;
  ai_bandwidth_pressure: string | null;
  ai_buyer_persona: string | null;
  ai_outreach_angle: string | null;
  ai_cold_email: string | null;
  ai_linkedin_message: string | null;
  ai_whatsapp_message: string | null;
  job_postings: JobPosting[];
  campaign_name: string | null;
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PriorityCount {
  priority: string;
  count: number;
}

export interface DashboardStats {
  total_campaigns: number;
  total_leads: number;
  avg_score: number;
  priority_breakdown: PriorityCount[];
  top_leads: Lead[];
  leads_with_decision_maker: number;
  total_open_jobs: number;
}

export interface ResearchRun {
  id: number;
  campaign_id: number;
  status: string;
  companies_found: number;
  leads_created: number;
  error: string | null;
  log: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface IntegrationSettings {
  openai_api_key_set: boolean;
  openai_base_url: string | null;
  openai_model: string | null;
  firecrawl_api_key_set: boolean;
  jobspy_enabled: boolean;
  hunter_api_key_set: boolean;
  zerobounce_api_key_set: boolean;
  apollo_api_key_set: boolean;
  reacher_api_url: string | null;
  baserow_api_url: string | null;
  baserow_api_key_set: boolean;
  twenty_api_url: string | null;
  twenty_api_key_set: boolean;
  hubspot_api_key_set: boolean;
  n8n_webhook_url: string | null;
}
