import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLang } from "../contexts/LanguageContext";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { SeverityBadge, StatusBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ChevronDown, Copy, ArrowLeft, Bot, AlertTriangle } from "lucide-react";

export default function AlertDetail() {
  const { alertId } = useParams<{ alertId: string }>();
  const navigate = useNavigate();
  const { T } = useLang();
  const [alert, setAlert] = useState<api.Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState<api.AnalyzeResponse | null>(null);
  const [rawOpen, setRawOpen] = useState(false);

  useEffect(() => {
    if (!alertId) return;
    setLoading(true);
    api.get<api.Alert>(`/alerts/${alertId}`)
      .then((r) => setAlert(r.data))
      .catch((e) => setError(e.response?.data?.detail || T("error")))
      .finally(() => setLoading(false));
  }, [alertId, T]);

  const runAnalysis = () => {
    if (!alertId) return;
    api.post<api.AnalyzeResponse>(`/alerts/${alertId}/analyze`, { force_refresh: true })
      .then((r) => setAnalysis(r.data))
      .catch((e) => setError(e.response?.data?.detail || T("error")));
  };

  if (loading) return <div className="p-4"><Skeleton className="h-8 w-1/2" /></div>;
  if (error) return <div className="p-4 text-red-400 flex items-center gap-2"><AlertTriangle className="w-5 h-5" /> <button onClick={() => window.location.reload()} className="underline text-soc-accent">{T("retry")}</button></div>;
  if (!alert) return <div className="p-4">Alert not found</div>;
  if (!alert) return <div className="p-4">Alert not found</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}><ArrowLeft className="w-4 h-4" /></Button>
          <h1 className="text-lg font-bold">{alert.alert_name || "Alert"}</h1>
        </div>
        <BadgeRow severity={alert.severity} status={alert.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader><h2 className="font-semibold">Alert Details</h2></CardHeader>
          <CardBody className="space-y-3">
            <DetailRow label="Alert ID" value={alert.vendor_alert_id} mono />
            <DetailRow label="Name" value={alert.alert_name || "—"} />
            <DetailRow label="Description" value={alert.description || "—"} />
            <DetailRow label="Category" value={alert.detection_category || "—"} />
            <DetailRow label="Type" value={alert.alert_type || "—"} />
            <DetailRow label="Endpoint" value={alert.host_name || "—"} />
            <DetailRow label="Host ID" value={alert.host_id || "—"} />
            <DetailRow label="User" value={alert.user_name || "—"} />
            <DetailRow label="Incident ID" value={alert.incident_id || "—"} />
            <DetailRow label="Detection Time" value={alert.detection_time || "—"} />
            <DetailRow label="Analysis Vendor" value={alert.analysis_vendor || "—"} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader><h2 className="font-semibold">AI Analysis</h2></CardHeader>
          <CardBody className="space-y-3">
            {analysis ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Model</span>
                  <span className="font-mono text-xs">{analysis.model_name}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Confidence</span>
                  <span className="font-mono text-xs">{Math.round((analysis.result.confidence ?? 0) * 100)}%</span>
                </div>
                <div className="pt-2 border-t border-soc-border/30">
                  <p className="text-sm text-gray-300">{analysis.result.summary}</p>
                </div>
                <p className="text-[10px] text-red-500/70 mt-1">AI-generated advisory — validate before acting.</p>
              </div>
            ) : (
              <p className="text-xs text-gray-500">No analysis yet.</p>
            )}
            <Button variant="outline" className="w-full" onClick={runAnalysis} disabled={loading}>
              <Bot className="w-4 h-4 mr-2" /> {loading ? "Analyzing..." : "Run AI Analysis"}
            </Button>
          </CardBody>
        </Card>
      </div>
        </Card>
      </div>

      <Card>
        <CardHeader><h2 className="font-semibold">Events & Evidence</h2></CardHeader>
        <CardBody>
          {alert.events && alert.events.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="soc-table">
                <thead><tr><th>Time</th><th>Type</th><th>Description</th><th>Event ID</th></tr></thead>
                <tbody>
                  {alert.events.map((e) => (
                    <tr key={e.id}>
                      <td className="text-xs text-gray-400">{e.event_time || "—"}</td>
                      <td className="text-xs">{e.event_type || "—"}</td>
                      <td className="text-xs">{e.description || "—"}</td>
                      <td className="font-mono text-xs text-gray-500">{e.vendor_event_id || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-gray-500">No events available.</p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="font-semibold">Raw API Response</h2>
          <Button variant="ghost" size="sm" onClick={() => setRawOpen(!rawOpen)}>
            {rawOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronDown className="w-4 h-4 rotate-180" />}
          </Button>
        </CardHeader>
        <CardBody className={rawOpen ? "" : "hidden"}>
          <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
            <AlertTriangle className="w-3 h-3" /> Access-controlled: raw vendor evidence retained for investigation.
          </div>
          <div className="bg-[#0d1117] rounded p-3 overflow-x-auto text-xs text-green-400 font-mono">
            <pre>{JSON.stringify(alert.raw_response, null, 2)}</pre>
            <Button variant="ghost" size="sm" className="mt-2" onClick={() => {
              navigator.clipboard.writeText(JSON.stringify(alert.raw_response, null, 2));
            }}>
              <Copy className="w-3 h-3 mr-1" /> Copy
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

function BadgeRow({ severity, status }: { severity?: string; status?: string }) {
  return (
    <div className="flex items-center gap-2">
      <SeverityBadge severity={severity} />
      <StatusBadge status={status} />
    </div>
  );
}

function DetailRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between text-sm border-b border-soc-border/30 pb-2 pt-1 last:pb-0">
      <span className="text-gray-500">{label}</span>
      <span className={`text-gray-300 ${mono ? "font-mono" : ""}`}>{value}</span>
    </div>
  );
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-soc-border/40 ${className || ""}`} />;
}