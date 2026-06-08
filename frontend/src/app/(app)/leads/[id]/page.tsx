"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Globe,
  MapPin,
  Mail,
  Briefcase,
  AlertTriangle,
  Users,
  Building2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { LeadDetail } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PriorityBadge } from "@/components/priority-badge";
import { CopyButton } from "@/components/copy-button";

function SignalChip({ active, label }: { active: boolean; label: string }) {
  return (
    <div
      className={`flex items-center gap-2 rounded-md border p-2 text-sm ${
        active ? "border-primary/30 bg-primary/5 text-foreground" : "bg-muted/40 text-muted-foreground"
      }`}
    >
      <span className={`size-2 rounded-full ${active ? "bg-primary" : "bg-slate-300"}`} />
      {label}
    </div>
  );
}

function MessageBlock({ title, value }: { title: string; value: string | null }) {
  if (!value) return null;
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">{title}</CardTitle>
        <CopyButton text={value} />
      </CardHeader>
      <CardContent>
        <pre className="whitespace-pre-wrap font-sans text-sm text-slate-700">{value}</pre>
      </CardContent>
    </Card>
  );
}

export default function LeadDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<LeadDetail>(`/api/leads/${id}`)
      .then(setLead)
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return <p className="text-destructive">{error}</p>;
  if (!lead) return <p className="text-muted-foreground">Loading lead…</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button asChild variant="ghost" size="icon">
          <Link href="/leads">
            <ArrowLeft />
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{lead.company_name}</h1>
            <PriorityBadge priority={lead.priority} />
          </div>
          <p className="text-muted-foreground">
            {[lead.industry, lead.region].filter(Boolean).join(" · ")}
            {lead.campaign_name ? ` · ${lead.campaign_name}` : ""}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Lead score</p>
          <p className="text-3xl font-bold">{lead.score}</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <Briefcase className="size-5 text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Open jobs</p>
              <p className="text-lg font-semibold">{lead.total_open_jobs}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <Users className="size-5 text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Recruiter/TA jobs</p>
              <p className="text-lg font-semibold">{lead.recruiter_jobs_open}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="size-5 text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">High-volume roles</p>
              <p className="text-lg font-semibold">{lead.high_volume_role_jobs}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <Building2 className="size-5 text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Employees</p>
              <p className="text-lg font-semibold">{lead.employee_count ?? "—"}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Score breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {lead.signals.length === 0 && <p className="text-sm text-muted-foreground">No scoring signals.</p>}
              {lead.signals.map((s, i) => (
                <div key={i} className="flex items-center justify-between rounded-md border p-2.5 text-sm">
                  <span>{s.label}</span>
                  <Badge>+{s.points}</Badge>
                </div>
              ))}
              <div className="flex items-center justify-between border-t pt-3 font-semibold">
                <span>Total</span>
                <span>{lead.score}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Hiring signals</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2 sm:grid-cols-2">
              <SignalChip active={lead.recruiter_jobs_open > 0} label="Hiring recruiters / TA" />
              <SignalChip active={lead.recruiter_jobs_open > 1} label="Hiring multiple recruiters" />
              <SignalChip active={lead.ta_coordinator_jobs > 0} label="TA coordinator / recruitment ops" />
              <SignalChip active={lead.has_urgent_hiring} label="Urgent hiring keywords" />
              <SignalChip active={lead.has_multiple_locations} label="Multiple locations" />
              <SignalChip active={lead.high_volume_role_jobs > 0} label="High-volume roles" />
              <SignalChip active={lead.has_stale_jobs} label="Repeated / stale jobs" />
              <SignalChip active={!!lead.decision_maker_name} label="Decision-maker found" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sample open jobs ({lead.job_postings.length})</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Tags</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lead.job_postings.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell className="font-medium">{job.title}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{job.location}</TableCell>
                      <TableCell className="space-x-1">
                        {job.is_recruiter_role && <Badge variant="secondary">Recruiter</Badge>}
                        {job.is_ta_coordinator && <Badge variant="secondary">TA Ops</Badge>}
                        {job.is_high_volume_role && <Badge variant="outline">High-volume</Badge>}
                        {job.is_urgent && <Badge variant="destructive">Urgent</Badge>}
                        {job.is_stale && <Badge variant="outline">Stale</Badge>}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Company</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {lead.website && (
                <a href={lead.website} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-primary hover:underline">
                  <Globe className="size-4" /> {lead.website}
                </a>
              )}
              {lead.careers_url && (
                <a href={lead.careers_url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-primary hover:underline">
                  <Briefcase className="size-4" /> Careers page
                </a>
              )}
              {lead.locations?.length > 0 && (
                <div className="flex items-start gap-2">
                  <MapPin className="mt-0.5 size-4 text-muted-foreground" />
                  <span>{lead.locations.join(", ")}</span>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Decision-maker</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {lead.decision_maker_name ? (
                <>
                  <p className="font-medium">{lead.decision_maker_name}</p>
                  <p className="text-muted-foreground">{lead.decision_maker_title}</p>
                  {lead.decision_maker_email && (
                    <div className="flex items-center gap-2">
                      <Mail className="size-4 text-muted-foreground" />
                      <span>{lead.decision_maker_email}</span>
                      {lead.decision_maker_email_status && (
                        <Badge variant="outline" className="text-xs">
                          {lead.decision_maker_email_status}
                        </Badge>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground">No decision-maker identified.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-xl font-semibold">AI outreach (drafts only)</h2>
        <Tabs defaultValue="insights">
          <TabsList>
            <TabsTrigger value="insights">Insights</TabsTrigger>
            <TabsTrigger value="email">Cold email</TabsTrigger>
            <TabsTrigger value="linkedin">LinkedIn</TabsTrigger>
            <TabsTrigger value="whatsapp">WhatsApp</TabsTrigger>
          </TabsList>
          <TabsContent value="insights" className="space-y-4">
            <MessageBlock title="Pain hypothesis" value={lead.ai_pain_hypothesis} />
            <MessageBlock title="Recruiter bandwidth pressure" value={lead.ai_bandwidth_pressure} />
            <MessageBlock title="Best buyer persona" value={lead.ai_buyer_persona} />
            <MessageBlock title="Outreach angle" value={lead.ai_outreach_angle} />
          </TabsContent>
          <TabsContent value="email">
            <MessageBlock title="Cold email" value={lead.ai_cold_email} />
          </TabsContent>
          <TabsContent value="linkedin">
            <MessageBlock title="LinkedIn message" value={lead.ai_linkedin_message} />
          </TabsContent>
          <TabsContent value="whatsapp">
            <MessageBlock title="WhatsApp message" value={lead.ai_whatsapp_message} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
