import { useEffect, useState } from "react";
import { useLang } from "../contexts/LanguageContext";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { SeverityBadge, StatusBadge } from "../components/ui/Badge";
import { AlertTriangle, ShieldAlert, Clock, RefreshCw } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Skeleton } from "../components/ui/Skeleton";

export default function Dashboard() {
  const { T } = useLang();
  const [data, setData] = useState<api.DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<api.DashboardSummary>("/dashboard/summary")
      .then((r) => setData(r.data))
      .catch((e) => setError(e.response?.data?.detail || T("error")))
      .finally(() => setLoading(false));
  }, [T]);

  if (loading) return <div className="space-y-4"><Skeleton className="h-10 w-3/4" /><Skeleton className="h-32" /></div>;
  if (error) return <div className="p-4 text-red-400">{error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{T("app_name")}</h1>
          <p className="text-gray-400 text-sm">{T("ai_disclaimer")}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => window.location.reload()}>
            <RefreshCw className="w-4 h-4 mr-2" /> {T("sync_now")}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title={T("total_alerts")} value={data.total_alerts} icon={<AlertTriangle className="w-5 h-5" />} color="text-cyan-400" />
        <MetricCard title={T("open_incidents")} value={data.open_incidents} icon={<ShieldAlert className="w-5 h-5" />} color="text-red-400" />
        <MetricCard title={T("critical_high")} value={data.critical_high_alerts} icon={null} color="text-orange-400" />
        <MetricCard title={T("last_sync")} value={data.last_sync_time ? new Date(data.last_sync_time).toLocaleString() : "—"} icon={<Clock className="w-5 h-5" />} color="text-gray-400" />
      </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader><h2 className="font-semibold">{T("ai_summary")}</h2></CardHeader>
          <CardBody>
            {data.ai_executive_summary ? (
              <div className="text-sm text-gray-300">
                <p className="mb-2">{data.ai_executive_summary.summary || T("no_data")}</p>
                <p className="text-xs text-gray-500">{`Confidence: ${(data.ai_executive_summary.confidence ?? 0) * 100}% · Model: ${data.ai_executive_summary.model_name || "—"}`}</p>
              </div>
            ) : (
              <p className="text-xs text-gray-500">No AI analysis available yet.</p>
            )}
            <p className="mt-2 text-xs text-red-500/70">{T("disclaimer")}</p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader><h2 className="font-semibold">Sync Status</h2></CardHeader>
          <CardBody className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400">Connection</p>
              <p className={`font-medium ${data.sync_status === "configured" ? "text-green-400" : data.sync_status === "demo" ? "text-yellow-400" : "text-red-400"}`}>
                {data.sync_status}
              </p>
            </div>
            <p className="text-xs text-gray-500">Demo: {data.demo_mode ? "on" : "off"}</p>
          </CardBody>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <StatCard title="Alerts Over Time" data={data.alerts_over_time} />
        <StatCard title="Severity Distribution" data={Object.entries(data.severity_distribution).map(([name, count]) => ({ name, count }))} />
        <StatCard title="Incident Status" data={Object.entries(data.incident_status_distribution).map(([name, count]) => ({ name, count }))} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StatCard title="Most Affected Endpoints" data={data.top_endpoints.map((e) => ({ name: e.endpoint || "—", count: e.count }))} />
        <StatCard title="Detection Categories" data={data.top_detection_categories.map((c) => ({ name: c.category || "—", count: c.count }))} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentTable title="Recent Alerts" items={data.recent_alerts.map((a) => ({ id: a.vendor_alert_id, name: a.alert_name || "—", severity: a.severity || "—", host: a.host_name || "—", time: a.detection_time || "—", status: a.status || "—" }))} />
        <RecentTable title="Recent Incidents" items={data.recent_incidents.map((i) => ({ id: i.vendor_incident_id, name: i.incident_name || "—", severity: i.severity || "—", host: i.host_name || "—", time: i.detection_time || "—", status: i.status || "—" }))} />
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon, color }: { title: string; value: React.ReactNode; icon: React.ReactNode | null; color: string }) {
  return (
    <Card>
      <CardBody className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-400 uppercase">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
        {icon && <div className="w-10 h-10 rounded bg-white/5 flex items-center justify-center">{React.cloneElement(icon, { className: `${color} w-5 h-5` })}</div>}
      </div>
    </Card>
  );
}

function StatCard({ title, data }: { title: string; data: Array<{ name: string; count: number }> }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  return (
    <Card>
      <CardHeader><h2 className="font-semibold">{title}</h2></CardHeader>
      <CardBody>
        <div className="space-y-2">
          {data.slice(0, 6).map((d) => (
            <div key={d.name} className="flex items-center justify-between text-sm">
              <span className="text-gray-400">{d.name}</span>
              <span className="font-mono text-gray-200">{d.count}</span>
            </div>
          ))}
          <div className="pt-2 border-t border-soc-border/30 text-xs text-gray-500">
            Total: {total}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function RecentTable({ title, items }: { title: string; items: Array<{ id: string; name: string; severity: string; host: string; time: string; status: string }> }) {
  return (
    <Card>
      <CardHeader><h2 className="font-semibold">{title}</h2></CardHeader>
      <CardBody>
        {items.length === 0 ? <p className="text-xs text-gray-500">{T("empty_alerts")}</p> : (
          <div className="overflow-x-auto">
            <table className="soc-table">
              <thead><tr><th>ID</th><th>Name</th><th>Severity</th><th>Host</th><th>Time</th><th>Status</th></tr></thead>
              <tbody>
                {items.map((it) => (
                  <tr key={it.id}>
                    <td className="font-mono text-xs text-gray-400">{it.id}</td>
                    <td className="text-xs">{it.name}</td>
                    <td><SeverityBadge severity={it.severity} /></td>
                    <td className="text-xs">{it.host}</td>
                    <td className="text-xs text-gray-400">{it.time}</td>
                    <td><StatusBadge status={it.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardBody>
    </Card>
  );
}