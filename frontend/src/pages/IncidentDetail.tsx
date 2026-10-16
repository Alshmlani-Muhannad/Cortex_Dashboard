import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLang } from "../contexts/LanguageContext";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { SeverityBadge, StatusBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ChevronDown, Copy, ArrowLeft, Bot, ShieldAlert, Send, Clock } from "lucide-react";

export default function IncidentDetail() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const navigate = useNavigate();
  const { T } = useLang();
  const [inc, setInc] = useState<api.Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState<api.AnalyzeResponse | null>(null);
  const [rawOpen, setRawOpen] = useState(false);
  const [timeline, setTimeline] = useState<Array<any>>([]);
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [chatInput, setChatInput] = useState("");

  useEffect(() => {
    if (!incidentId) return;
    setLoading(true);
    Promise.all([
      api.get<api.Incident>(`/incidents/${incidentId}`),
      api.get<{ timeline: Array<any> }>(`/incidents/${incidentId}/timeline`).catch(() => ({ timeline: [] })),
    ])
      .then(([r1, r2]) => {
        setInc(r1.data);
        setTimeline(r2.data.timeline || []);
      })
      .catch((e) => setError(e.response?.data?.detail || T("error")))
      .finally(() => setLoading(false));
  }, [incidentId, T]);

  const runAnalysis = () => {
    if (!incidentId) return;
    api.post<api.AnalyzeResponse>(`/incidents/${incidentId}/analyze`, { force_refresh: true })
      .then((r) => setAnalysis(r.data))
      .catch((e) => setError(e.response?.data?.detail || T("error")));
  };

  const sendChat = () => {
    if (!chatInput.trim() || !incidentId) return;
    const userMsg = chatInput;
    setChatInput("");
    setMessages((p) => [...p, { role: "user", content: userMsg }]);
    api.post<{ response: string }>(`/incidents/${incidentId}/chat`, { message: userMsg })
      .then((r) => setMessages((p) => [...p, { role: "assistant", content: r.data.response }]))
      .catch((e) => setMessages((p) => [...p, { role: "assistant", content: e.response?.data?.detail || T("error") }]));
  };

  if (loading) return <div className="p-4"><Skeleton className="h-8 w-1/2" /></div>;
  if (error) return <div className="p-4 text-red-400">{error}</div>;
  if (!inc) return <div className="p-4">Incident not found</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}><ArrowLeft className="w-4 h-4" /></Button>
          <h1 className="text-lg font-bold">{inc.incident_name || "Incident"}</h1>
        </div>
        <div className="flex items-center gap-2">
          <SeverityBadge severity={inc.severity} />
          <StatusBadge status={inc.status} />
        </div>
      </div>
      </div>),

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader><h2 className="font-semibold">Incident Details</h2></CardHeader>
          <CardBody className="space-y-3">
            <DetailRow label="Incident ID" value={inc.vendor_incident_id} mono />
            <DetailRow label="Name" value={inc.incident_name || "—"} />
            <DetailRow label="Description" value={inc.description || "—"} />
            <DetailRow label="Severity" value={inc.severity || "—"} />
            <DetailRow label="Status" value={inc.status || "—"} />
            <DetailRow label="Endpoint" value={inc.host_name || "—"} />
            <DetailRow label="User" value={inc.user_name || "—"} />
            <DetailRow label="Detection Time" value={inc.detection_time || "—"} />
            <DetailRow label="Last Update" value={inc.last_update_time || "—"} />
            <DetailRow label="Linked Alerts" value={(inc.alerts?.length ?? 0).toString()} />
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

      <Card>
        <CardHeader><h2 className="font-semibold">Linked Alerts</h2></CardHeader>
        <CardBody>
        <CardBody>
          {inc.alerts && inc.alerts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="soc-table">
                <thead><tr><th>Alert ID</th><th>Name</th><th>Severity</th><th>Category</th><th>Endpoint</th><th>Status</th><th></th></tr></thead>
                <tbody>
                  {inc.alerts.map((a) => (
                    <tr key={a.vendor_alert_id} className="hover:bg-white/5 cursor-pointer" onClick={() => { window.location.href = `/alerts/${a.vendor_alert_id}`; }}>
                      <td className="font-mono text-xs text-gray-400">{a.vendor_alert_id}</td>
                      <td className="text-xs">{a.alert_name || "—"}</td>
                      <td><SeverityBadge severity={a.severity} /></td>
                      <td className="text-xs">{a.detection_category || "—"}</td>
                      <td className="text-xs">{a.host_name || "—"}</td>
                      <td><StatusBadge status={a.status} /></td>
                      <td className="text-right"><Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); window.location.href = `/alerts/${a.vendor_alert_id}`; }}>View</Button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-gray-500">No linked alerts.</p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader><h2 className="font-semibold"><Clock className="w-4 h-4 mr-2" /> Timeline</h2></CardHeader>
        <CardBody>
          {timeline.length > 0 ? (
            <div className="space-y-3">
              {timeline.map((e, i) => (
                <div key={i} className="flex gap-3 text-sm border-l-2 border-soc-border pl-3 py-2">
                  <span className="text-gray-500 font-mono text-xs w-24">{e.time || "—"}</span>
                  <div>
                    <div className="font-medium text-gray-200">{e.event_type || e.description || "Event"}</div>
                    <div className="text-xs text-gray-400">{e.description || ""}</div>
                    {e.vendor_alert_id && <div className="text-[10px] text-gray-600 mt-1">Alert: {e.vendor_alert_id}</div>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500">No timeline events available.</p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="font-semibold"><Bot className="w-4 h-4 mr-2" /> AI Investigation Chat</h2>
        </CardHeader>
        <CardBody className="space-y-3">
          <div className="h-64 overflow-y-auto border border-soc-border/30 rounded p-3 space-y-3 bg-white/5">
            {messages.length === 0 ? (
              <p className="text-xs text-gray-500">Ask about this incident (evidence-based).</p>
            ) : (
              messages.map((m, i) => (
                <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] p-2 rounded text-xs ${
                    m.role === "user" ? "bg-soc-accent/10 text-soc-accent ml-auto" : "bg-white/5 text-gray-300"
                  }`}>{m.content}</div>
                </div>
              ))
            )}
          </div>
          <div className="flex gap-2">
            <Input value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Ask about this incident..." onKeyDown={(e) => e.key === "Enter" && sendChat()} />
            <Button variant="primary" onClick={sendChat} disabled={!chatInput.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-[10px] text-gray-500">Answers use only stored incident evidence.</p>
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
          <div className="bg-[#0d1117] rounded p-3 overflow-x-auto text-xs text-green-400 font-mono">
            <pre>{JSON.stringify(inc.raw_response, null, 2)}</pre>
          </div>
        </CardBody>
      </Card>
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