import { useState, useEffect } from "react";
import { useLang } from "../contexts/LanguageContext";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { RefreshCw } from "lucide-react";

export default function Incidents() {
  const { T } = useLang();
  const [filters, setFilters] = useState({
    severity: "", status: "", endpoint: "", search: "",
    sort_field: "detection_time", sort_order: "desc", page: 1, page_size: 25,
  });
  const [data, setData] = useState<api.Paginated<api.Incident> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetch = () => {
    setLoading(true);
    api.get<api.Paginated<api.Incident>>("/incidents", { params: filters })
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

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Incidents</h1>
          <p className="text-xs text-gray-500">Investigate synchronized Cortex XDR incidents.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetch}>
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardBody className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Severity</label>
              <Input value={filters.severity} onChange={(e) => setFilter("severity", e.target.value)} placeholder="Severity" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Status</label>
              <Input value={filters.status} onChange={(e) => setFilter("status", e.target.value)} placeholder="Status" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Endpoint</label>
              <Input value={filters.endpoint} onChange={(e) => setFilter("endpoint", e.target.value)} placeholder="Endpoint" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Search</label>
              <Input value={filters.search} onChange={(e) => setFilter("search", e.target.value)} placeholder="Name / ID" />
            </div>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <div className="overflow-x-auto">
            <table className="soc-table">
              <thead><tr><th>ID</th><th>Name</th><th>Severity</th><th>Status</th><th>Endpoint</th><th>User</th><th>Detection Time</th><th>Alerts</th><th></th></tr></thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr><td colSpan={9} className="text-xs text-gray-500 py-4 text-center">No incidents found.</td></tr>
                ) : (
                  data.items.map((i) => (
                    <tr key={i.id} className="hover:bg-white/5 cursor-pointer" onClick={() => { window.location.href = `/incidents/${i.id}`; }}>
                      <td className="font-mono text-xs text-gray-400">{i.vendor_incident_id}</td>
                      <td className="text-xs">{i.incident_name || "—"}</td>
                      <td><StatusBadge status={i.severity} /></td>
                      <td><StatusBadge status={i.status} /></td>
                      <td className="text-xs">{i.host_name || "—"}</td>
                      <td className="text-xs text-gray-400">{i.user_name || "—"}</td>
                      <td className="text-xs text-gray-400">{i.detection_time ? new Date(i.detection_time).toLocaleString() : "—"}</td>
                      <td className="text-xs text-gray-400">{i.alerts?.length ?? 0}</td>
                      <td className="text-right"><Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); window.location.href = `/incidents/${i.id}`; }}>View</Button></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>

      <div className="flex items-center justify-between text-xs text-gray-400">
        <div>Page {data.page} of {data.total_pages} ({data.total} incidents)</div>
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