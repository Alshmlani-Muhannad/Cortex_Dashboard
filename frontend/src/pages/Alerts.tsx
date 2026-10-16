import { useState, useEffect } from "react";
import { useLang } from "../contexts/LanguageContext";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { SeverityBadge, StatusBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { RefreshCw } from "lucide-react";

export default function Alerts() {
  const { T } = useLang();
  const [filters, setFilters] = useState({
    severity: "", time_range: "", endpoint: "", detection_category: "", status: "", incident_id: "", search: "",
    sort_field: "detection_time", sort_order: "desc", page: 1, page_size: 25,
  });
  const [data, setData] = useState<api.Paginated<api.Alert> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetch = () => {
    setLoading(true);
    api.get<api.Paginated<api.Alert>>("/alerts", { params: filters })
      .then((r) => setData(r.data))
      .catch((e) => setError(e.response?.data?.detail || T("error")))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetch(); }, [JSON.stringify(filters), T]);

  const setFilter = (k: string, v: string) => {
    setFilters((p) => ({ ...p, [k]: v, page: 1 }));
  };

  if (loading) return <div className="p-4"><Skeleton className="h-8 w-1/2" /></div>;
  if (error) return <div className="p-4 text-red-400">{error}</div>;
  if (!data) return null;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">{T("alerts_explorer")}</h1>
          <p className="text-xs text-gray-500">Search and filter synchronized Cortex XDR alerts.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetch}>
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardBody className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Severity</label>
              <select className="soc-input" value={filters.severity} onChange={(e) => setFilter("severity", e.target.value)}>
                <option value="">All</option>
                {["critical","high","medium","low","info"].map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Time range</label>
              <select className="soc-input" value={filters.time_range} onChange={(e) => setFilter("time_range", e.target.value)}>
                <option value="">All</option><option value="24h">24h</option><option value="7d">7d</option><option value="30d">30d</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Endpoint</label>
              <Input value={filters.endpoint} onChange={(e) => setFilter("endpoint", e.target.value)} placeholder="Endpoint" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Category</label>
              <Input value={filters.detection_category} onChange={(e) => setFilter("detection_category", e.target.value)} placeholder="Category" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Status</label>
              <Input value={filters.status} onChange={(e) => setFilter("status", e.target.value)} placeholder="Status" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Incident ID</label>
              <Input value={filters.incident_id} onChange={(e) => setFilter("incident_id", e.target.value)} placeholder="Incident ID" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <label className="text-xs text-gray-400">Search</label>
            <Input value={filters.search} onChange={(e) => setFilter("search", e.target.value)} placeholder="alert name, host, user..." className="w-64" />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <div className="overflow-x-auto">
            <table className="soc-table">
              <thead>
                <tr>
                  <th>ID</th><th>Alert Name</th><th>Severity</th><th>Category</th><th>Endpoint</th><th>User</th><th>Detection Time</th><th>Status</th><th>Incident</th><th></th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr><td colSpan={10} className="text-xs text-gray-500 py-4 text-center">No alerts found.</td></tr>
                ) : (
                  data.items.map((a) => (
                    <tr key={a.id} className="hover:bg-white/5 cursor-pointer" onClick={() => { window.location.href = `/alerts/${a.id}`; }}>
                      <td className="font-mono text-xs text-gray-400">{a.vendor_alert_id}</td>
                      <td className="text-xs">{a.alert_name || "—"}</td>
                      <td><SeverityBadge severity={a.severity} /></td>
                      <td className="text-xs">{a.detection_category || "—"}</td>
                      <td className="text-xs">{a.host_name || "—"}</td>
                      <td className="text-xs text-gray-400">{a.user_name || "—"}</td>
                      <td className="text-xs text-gray-400">{a.detection_time ? new Date(a.detection_time).toLocaleString() : "—"}</td>
                      <td><StatusBadge status={a.status} /></td>
                      <td className="text-xs">{a.incident_id || "—"}</td>
                      <td className="text-right"><Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); window.location.href = `/alerts/${a.id}`; }}>View</Button></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>

      <div className="flex items-center justify-between text-xs text-gray-400">
        <div>Page {data.page} of {data.total_pages} ({data.total} alerts)</div>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" disabled={data.page === 1} onClick={() => setFilter("page", String(data.page - 1))}>Prev</Button>
          <Button variant="ghost" size="sm" disabled={data.page >= data.total_pages} onClick={() => setFilter("page", String(data.page + 1))}>Next</Button>
        </div>
      </div>
    </div>
  );
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-soc-border/40 ${className || ""}`} />;
}