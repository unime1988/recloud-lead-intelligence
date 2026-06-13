"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Campaign } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

function parseList(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function NewCampaignPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    industry: "",
    region: "",
    min_employee_count: 0,
    job_keywords: "software engineer, support, sales",
    recruiter_keywords: "recruiter, talent acquisition",
    high_volume_role_keywords: "sales, support, bpo, operations",
    target_decision_maker_titles: "Head of Talent Acquisition, VP People, Director HR",
  });

  function update(key: string, value: string | number) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const campaign = await api<Campaign>("/api/campaigns", {
        method: "POST",
        body: {
          name: form.name,
          industry: form.industry || null,
          region: form.region || null,
          min_employee_count: Number(form.min_employee_count) || 0,
          job_keywords: parseList(form.job_keywords),
          recruiter_keywords: parseList(form.recruiter_keywords),
          high_volume_role_keywords: parseList(form.high_volume_role_keywords),
          target_decision_maker_titles: parseList(form.target_decision_maker_titles),
        },
      });
      toast.success("Campaign created. Starting research…");
      await api(`/api/campaigns/${campaign.id}/research`, { method: "POST" }).catch(() => null);
      router.push(`/leads?campaign_id=${campaign.id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create campaign");
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button asChild variant="ghost" size="icon">
          <Link href="/campaigns">
            <ArrowLeft />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">New campaign</h1>
          <p className="text-muted-foreground">Describe the companies you want to target.</p>
        </div>
      </div>

      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>Campaign inputs</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Campaign name *</Label>
              <Input id="name" required value={form.name} onChange={(e) => update("name", e.target.value)} placeholder="India BPO Hiring Surge" />
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="industry">Industry</Label>
                <Input id="industry" value={form.industry} onChange={(e) => update("industry", e.target.value)} placeholder="BPO" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="region">Region / country</Label>
                <Input id="region" value={form.region} onChange={(e) => update("region", e.target.value)} placeholder="India" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="min_emp">Min employees</Label>
                <Input
                  id="min_emp"
                  type="number"
                  min={0}
                  value={form.min_employee_count}
                  onChange={(e) => update("min_employee_count", e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="jk">Job keywords</Label>
              <Textarea id="jk" value={form.job_keywords} onChange={(e) => update("job_keywords", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="rk">Recruiter keywords</Label>
              <Textarea id="rk" value={form.recruiter_keywords} onChange={(e) => update("recruiter_keywords", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="hv">High-volume role keywords</Label>
              <Textarea id="hv" value={form.high_volume_role_keywords} onChange={(e) => update("high_volume_role_keywords", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dm">Target decision-maker titles</Label>
              <Textarea id="dm" value={form.target_decision_maker_titles} onChange={(e) => update("target_decision_maker_titles", e.target.value)} />
            </div>
            <p className="text-xs text-muted-foreground">Separate multiple values with commas or new lines.</p>
            <div className="flex gap-2">
              <Button type="submit" disabled={loading}>
                {loading ? "Creating…" : "Create & run research"}
              </Button>
              <Button type="button" variant="outline" asChild>
                <Link href="/campaigns">Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
