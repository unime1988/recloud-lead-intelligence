"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { IntegrationSettings } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

interface KeyField {
  name: string;
  label: string;
  placeholder: string;
  secret?: boolean;
  setFlag?: keyof IntegrationSettings;
}

const SECTIONS: { title: string; description: string; fields: KeyField[] }[] = [
  {
    title: "AI generation (OpenAI-compatible)",
    description: "Used to generate outreach drafts. Falls back to templates when unset.",
    fields: [
      { name: "openai_api_key", label: "API key", placeholder: "sk-…", secret: true, setFlag: "openai_api_key_set" },
      { name: "openai_base_url", label: "Base URL", placeholder: "https://api.openai.com/v1" },
      { name: "openai_model", label: "Model", placeholder: "gpt-4.1-mini" },
    ],
  },
  {
    title: "Firecrawl (career page scraping)",
    description: "Optional. Only public pages are scraped, respecting robots.txt.",
    fields: [{ name: "firecrawl_api_key", label: "API key", placeholder: "fc-…", secret: true, setFlag: "firecrawl_api_key_set" }],
  },
  {
    title: "Email verification",
    description: "Reacher / ZeroBounce / Hunter for decision-maker email validation.",
    fields: [
      { name: "reacher_api_url", label: "Reacher API URL", placeholder: "http://reacher:8080" },
      { name: "zerobounce_api_key", label: "ZeroBounce key", placeholder: "…", secret: true, setFlag: "zerobounce_api_key_set" },
      { name: "hunter_api_key", label: "Hunter key", placeholder: "…", secret: true, setFlag: "hunter_api_key_set" },
    ],
  },
  {
    title: "CRM & webhook export",
    description: "Optional CRM sync and n8n/webhook export. Disabled by default.",
    fields: [
      { name: "n8n_webhook_url", label: "n8n webhook URL", placeholder: "https://…" },
      { name: "hubspot_api_key", label: "HubSpot token", placeholder: "…", secret: true, setFlag: "hubspot_api_key_set" },
      { name: "baserow_api_url", label: "Baserow API URL", placeholder: "https://…" },
      { name: "twenty_api_url", label: "Twenty CRM API URL", placeholder: "https://…" },
    ],
  },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<IntegrationSettings | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api<IntegrationSettings>("/api/settings")
      .then((s) => {
        setSettings(s);
        setValues({
          openai_base_url: s.openai_base_url || "",
          openai_model: s.openai_model || "",
          reacher_api_url: s.reacher_api_url || "",
          n8n_webhook_url: s.n8n_webhook_url || "",
          baserow_api_url: s.baserow_api_url || "",
          twenty_api_url: s.twenty_api_url || "",
        });
      })
      .catch((e) => toast.error(e.message));
  }, []);

  async function save() {
    setSaving(true);
    try {
      const body: Record<string, string> = {};
      for (const [k, v] of Object.entries(values)) {
        if (v !== "") body[k] = v;
      }
      const updated = await api<IntegrationSettings>("/api/settings", { method: "PUT", body });
      setSettings(updated);
      setValues((prev) => {
        const next = { ...prev };
        // Clear secret inputs after save (they are write-only).
        for (const section of SECTIONS) {
          for (const f of section.fields) {
            if (f.secret) next[f.name] = "";
          }
        }
        return next;
      });
      toast.success("Settings saved");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  if (!settings) return <p className="text-muted-foreground">Loading settings…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure integration API keys. Keys are stored per account and never returned to the browser.
        </p>
      </div>

      {SECTIONS.map((section) => (
        <Card key={section.title}>
          <CardHeader>
            <CardTitle className="text-base">{section.title}</CardTitle>
            <CardDescription>{section.description}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {section.fields.map((f) => {
              const isSet = f.setFlag ? Boolean(settings[f.setFlag]) : false;
              return (
                <div key={f.name} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor={f.name}>{f.label}</Label>
                    {f.secret && (
                      <Badge variant={isSet ? "secondary" : "outline"} className="text-xs">
                        {isSet ? "Set" : "Not set"}
                      </Badge>
                    )}
                  </div>
                  <Input
                    id={f.name}
                    type={f.secret ? "password" : "text"}
                    placeholder={f.secret && isSet ? "•••••••• (leave blank to keep)" : f.placeholder}
                    value={values[f.name] ?? ""}
                    onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
                  />
                </div>
              );
            })}
          </CardContent>
        </Card>
      ))}

      <div className="flex justify-end">
        <Button onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save settings"}
        </Button>
      </div>
    </div>
  );
}
