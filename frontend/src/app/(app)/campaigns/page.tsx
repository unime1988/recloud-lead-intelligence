"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Play, Trash2, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Campaign } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<number | null>(null);

  async function load() {
    const data = await api<Campaign[]>("/api/campaigns");
    setCampaigns(data);
    setLoading(false);
  }

  useEffect(() => {
    load().catch((e) => {
      toast.error(e.message);
      setLoading(false);
    });
  }, []);

  async function runResearch(id: number) {
    setRunning(id);
    try {
      await api(`/api/campaigns/${id}/research`, { method: "POST" });
      toast.success("Research started. Leads will appear shortly.");
      // Poll a few times for completion.
      setTimeout(load, 3000);
      setTimeout(load, 7000);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed");
    } finally {
      setTimeout(() => setRunning(null), 7000);
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this campaign and its leads?")) return;
    try {
      await api(`/api/campaigns/${id}`, { method: "DELETE" });
      toast.success("Campaign deleted");
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Campaigns</h1>
          <p className="text-muted-foreground">Define your ICP and run lead research.</p>
        </div>
        <Button asChild>
          <Link href="/campaigns/new">
            <Plus /> New campaign
          </Link>
        </Button>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Loading…</p>
      ) : campaigns.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <p className="text-muted-foreground">No campaigns yet.</p>
            <Button asChild>
              <Link href="/campaigns/new">
                <Plus /> Create your first campaign
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {campaigns.map((c) => (
            <Card key={c.id}>
              <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{c.name}</h3>
                    <Badge variant="secondary">{c.status}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {[c.industry, c.region].filter(Boolean).join(" · ") || "No targeting set"} ·{" "}
                    {c.leads_count} leads · min {c.min_employee_count} employees
                    {c.company_type && c.company_type !== "all" && (
                      <> · <span className="font-medium text-primary">{c.company_type.replace(/_/g, " ")}</span></>
                    )}
                  </p>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {c.job_keywords.slice(0, 4).map((k) => (
                      <Badge key={k} variant="outline" className="text-xs">
                        {k}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button size="sm" onClick={() => runResearch(c.id)} disabled={running === c.id}>
                    {running === c.id ? <Loader2 className="animate-spin" /> : <Play />}
                    Run research
                  </Button>
                  <Button asChild size="sm" variant="outline">
                    <Link href={`/leads?campaign_id=${c.id}`}>View leads</Link>
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => remove(c.id)}>
                    <Trash2 className="text-destructive" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
