import { useState, useEffect } from "react";
import { useLang } from "../contexts/LanguageContext";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ShieldCheck, RefreshCw, Bot, AlertTriangle } from "lucide-react";

export default function Settings() {
  const { T, lang, setLang, dir } = useLang();
  const [ai, setAi] = useState<api.AISettings | null>(null);
  const [intg, setIntg] = useState<api.SyncStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.get<api.AISettings>("/settings/ai").then(setAi).catch(() => setAi(null)),
      api.get<api.SyncStatus>("/sync/status").then(setIntg).catch(() => setIntg(null)),
    ]).catch((e) => setError(e.response?.data?.detail || T("error")));
  }, [T]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{T("settings")}</h1>
        <p className="text-gray-400 text-sm">Integration and AI configuration.</p>
      </div>

      <Card>
        <CardHeader><h2 className="font-semibold">Language</h2></CardHeader>
        <CardBody>
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-soc-accent" />
            <div>
              <p className="text-sm font-medium">{T("language")}</p>
              <p className="text-xs text-gray-500">Interface language and layout direction.</p>
            </div>
            <div className="ml-auto flex gap-2">
              <Button variant={lang === "en" ? "primary" : "outline"} size="sm" onClick={() => setLang("en")}>English</Button>
              <Button variant={lang === "ar" ? "primary" : "outline"} size="sm" onClick={() => setLang("ar")}>العربية</Button>
            </div>
          </div>
          <p className="mt-3 text-xs text-gray-500">Current layout direction: {dir === "rtl" ? "RTL (right-to-left)" : "LTR (left-to-right)"}</p>
        </CardBody>
      </Card>
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="font-semibold">Cortex XDR Integration</h2>
        </CardHeader>
        <CardBody className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span>Connection status</span>
            <span className={`font-medium ${intg?.connection_status === "configured" ? "text-green-400" : intg?.connection_status === "demo" ? "text-yellow-400" : "text-red-400"}`}>
              {intg?.connection_status === "configured" ? "Configured" : intg?.connection_status === "demo" ? "Demo mode" : "Not configured"}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span>Last sync</span>
            <span className="text-gray-400">{intg?.last_sync_time ? new Date(intg.last_sync_time).toLocaleString() : "—"}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span>Last job</span>
            <span className="text-gray-400">{intg?.last_job_status || "—"}</span>
          </div>
          {intg?.demo_mode && (
            <div className="p-3 rounded bg-yellow-900/20 border border-yellow-900/30 text-yellow-400 text-xs">
              <AlertTriangle className="w-4 h-4 mr-2" /> Running with labeled synthetic demo data. Real Cortex XDR data requires valid credentials in .env.
            </div>
          )}
          <div className="flex items-center justify-between text-sm">
            <span>Configured (backend)</span>
            <span className="text-gray-400">{intg?.configured ? "Yes" : "No"}</span>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><h2 className="font-semibold">AI Settings</h2></CardHeader>
        <CardBody className="space-y-3">
          {ai ? (
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-gray-400">Provider</label>
                  <p className="font-mono text-xs">{ai.provider}</p>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-gray-400">Model</label>
                  <Input value={ai.model} onChange={() => {}} disabled placeholder={ai.model} />
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>AI enabled</span>
                <span className="text-gray-400">{ai.enabled ? "Yes" : "No"}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Prompt version</span>
                <span className="font-mono text-xs text-gray-400">{ai.prompt_version}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Temperature</span>
                <span className="font-mono text-xs text-gray-400">{ai.temperature}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Max tokens</span>
                <span className="font-mono text-xs text-gray-400">{ai.max_tokens}</span>
              </div>
              {ai.demo_mode && (
                <div className="p-3 rounded bg-yellow-900/20 border border-yellow-900/30 text-yellow-400 text-xs">
                  <AlertTriangle className="w-4 h-4 mr-2" /> AI demo mode: structured synthetic analysis without calling an LLM.
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-500">Unable to load AI settings.</p>
          )}
        </CardBody>
      </Card>

      <div className="p-4 text-xs text-gray-500">
        <p><AlertTriangle className="w-3 h-3 mr-1 inline" /> Cortex API keys and LLM API keys are stored only on the backend and are never exposed to the browser.</p>
        <p>AI output is advisory and requires SOC analyst validation.</p>
      </div>
    </div>
  );
}