import { useMemo } from "react";

const SEVERITY_CLASSES: Record<string, string> = {
  critical: "badge-severity-critical",
  high: "badge-severity-high",
  medium: "badge-severity-medium",
  low: "badge-severity-low",
  info: "badge-severity-info",
};
const STATUS_CLASSES: Record<string, string> = {
  open: "badge-status-open",
  closed: "badge-status-closed",
};

export function SeverityBadge({ severity }: { severity?: string }) {
  const cls = useMemo(() => SEVERITY_CLASSES[(severity || "info").toLowerCase()] || "badge-severity-info", [severity]);
  return <span className={`badge ${cls}`}>{severity || "—"}</span>;
}

export function StatusBadge({ status }: { status?: string }) {
  const cls = useMemo(() => STATUS_CLASSES[(status || "").toLowerCase()] || "badge-status-open", [status]);
  return <span className={`badge ${cls}`}>{status || "—"}</span>;
}