"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Building2, Flame, Target, Users, Briefcase } from "lucide-react";
import { api } from "@/lib/api";
import type { DashboardStats } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PriorityBadge } from "@/components/priority-badge";
import { priorityColor } from "@/lib/utils";

function StatCard({ icon: Icon, label, value }: { icon: any; label: string; value: string | number }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <div className="flex size-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-semibold">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<DashboardStats>("/api/dashboard/stats")
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-destructive">{error}</p>;
  if (!stats) return <p className="text-muted-foreground">Loading dashboard…</p>;

  const maxCount = Math.max(1, ...stats.priority_breakdown.map((p) => p.count));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your lead pipeline and hiring signals.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard icon={Building2} label="Total leads" value={stats.total_leads} />
        <StatCard icon={Target} label="Campaigns" value={stats.total_campaigns} />
        <StatCard icon={Flame} label="Avg score" value={stats.avg_score} />
        <StatCard icon={Users} label="With decision-maker" value={stats.leads_with_decision_maker} />
        <StatCard icon={Briefcase} label="Total open jobs" value={stats.total_open_jobs} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Leads by priority</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {stats.priority_breakdown.map((p) => (
              <div key={p.priority} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <PriorityBadge priority={p.priority} />
                  <span className="font-medium">{p.count}</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={priorityColor(p.priority).split(" ")[0] + " h-full rounded-full"}
                    style={{ width: `${(p.count / maxCount) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top leads</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {stats.top_leads.length === 0 && (
              <p className="text-sm text-muted-foreground">No leads yet. Run a campaign to get started.</p>
            )}
            {stats.top_leads.map((lead) => (
              <Link
                key={lead.id}
                href={`/leads/${lead.id}`}
                className="flex items-center justify-between rounded-md border p-3 transition-colors hover:bg-slate-50"
              >
                <div>
                  <p className="font-medium">{lead.company_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {lead.total_open_jobs} open jobs · {lead.industry}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold">{lead.score}</span>
                  <PriorityBadge priority={lead.priority} />
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
