"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Search, Download, ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { api, apiUrl, getToken } from "@/lib/api";
import type { LeadListResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PriorityBadge } from "@/components/priority-badge";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

const PRIORITIES = ["", "Very Hot", "High", "Medium", "Low"];

function LeadsContent() {
  const searchParams = useSearchParams();
  const campaignId = searchParams.get("campaign_id");

  const [data, setData] = useState<LeadListResponse | null>(null);
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState("");
  const [minScore, setMinScore] = useState("");
  const [sortBy, setSortBy] = useState("score");
  const [sortDir, setSortDir] = useState("desc");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (campaignId) params.set("campaign_id", campaignId);
    if (search) params.set("search", search);
    if (priority) params.set("priority", priority);
    if (minScore) params.set("min_score", minScore);
    params.set("sort_by", sortBy);
    params.set("sort_dir", sortDir);
    params.set("page", String(page));
    params.set("page_size", "10");
    try {
      const res = await api<LeadListResponse>(`/api/leads?${params.toString()}`);
      setData(res);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to load leads");
    } finally {
      setLoading(false);
    }
  }, [campaignId, search, priority, minScore, sortBy, sortDir, page]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  function toggleSort(col: string) {
    if (sortBy === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(col);
      setSortDir("desc");
    }
    setPage(1);
  }

  async function exportCsv() {
    const params = new URLSearchParams();
    if (campaignId) params.set("campaign_id", campaignId);
    if (priority) params.set("priority", priority);
    if (search) params.set("search", search);
    try {
      const res = await fetch(apiUrl(`/api/export/leads.csv?${params.toString()}`), {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "recloud_leads.csv";
      a.click();
      URL.revokeObjectURL(url);
      toast.success("CSV downloaded");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Export failed");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Leads</h1>
          <p className="text-muted-foreground">
            {data ? `${data.total} leads` : "Loading…"}
            {campaignId ? " · filtered by campaign" : ""}
          </p>
        </div>
        <Button variant="outline" onClick={exportCsv}>
          <Download /> Export CSV
        </Button>
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative min-w-[220px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Search company, industry, region…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <Select
            className="w-40"
            value={priority}
            onChange={(e) => {
              setPriority(e.target.value);
              setPage(1);
            }}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p || "All priorities"}
              </option>
            ))}
          </Select>
          <Input
            type="number"
            className="w-32"
            placeholder="Min score"
            value={minScore}
            onChange={(e) => {
              setMinScore(e.target.value);
              setPage(1);
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <button className="flex items-center gap-1" onClick={() => toggleSort("company_name")}>
                    Company <ArrowUpDown className="size-3" />
                  </button>
                </TableHead>
                <TableHead>Industry / Region</TableHead>
                <TableHead>
                  <button className="flex items-center gap-1" onClick={() => toggleSort("total_open_jobs")}>
                    Open jobs <ArrowUpDown className="size-3" />
                  </button>
                </TableHead>
                <TableHead>Decision-maker</TableHead>
                <TableHead>
                  <button className="flex items-center gap-1" onClick={() => toggleSort("score")}>
                    Score <ArrowUpDown className="size-3" />
                  </button>
                </TableHead>
                <TableHead>Priority</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && (
                <TableRow>
                  <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                    Loading…
                  </TableCell>
                </TableRow>
              )}
              {!loading && data?.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                    No leads found.
                  </TableCell>
                </TableRow>
              )}
              {!loading &&
                data?.items.map((lead) => (
                  <TableRow key={lead.id} className="cursor-pointer">
                    <TableCell>
                      <Link href={`/leads/${lead.id}`} className="font-medium hover:underline">
                        {lead.company_name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {[lead.industry, lead.region].filter(Boolean).join(" · ")}
                    </TableCell>
                    <TableCell>{lead.total_open_jobs}</TableCell>
                    <TableCell>
                      {lead.decision_maker_name ? (
                        <span className="text-sm">
                          {lead.decision_maker_name}
                          <span className="block text-xs text-muted-foreground">{lead.decision_maker_title}</span>
                        </span>
                      ) : (
                        <Badge variant="outline">None</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-lg font-bold">{lead.score}</TableCell>
                    <TableCell>
                      <PriorityBadge priority={lead.priority} />
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {data.page} of {data.pages}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft /> Prev
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= data.pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next <ChevronRight />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function LeadsPage() {
  return (
    <Suspense fallback={<p className="text-muted-foreground">Loading…</p>}>
      <LeadsContent />
    </Suspense>
  );
}
