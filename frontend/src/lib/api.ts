import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT from localStorage on every request (kept out of Cortex credentials).
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("soc_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("soc_token");
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  },
);

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export interface Alert {
  id: string;
  vendor_alert_id: string;
  tenant_id?: string;
  alert_name?: string;
  description?: string;
  severity?: string;
  detection_category?: string;
  alert_type?: string;
  status?: string;
  creation_time?: string;
  detection_time?: string;
  analysis_time?: string;
  host_name?: string;
  host_id?: string;
  user_name?: string;
  incident_id?: string;
  analysis_vendor?: string;
  raw_response: any;
}

export interface Incident {
  id: string;
  vendor_incident_id: string;
  tenant_id?: string;
  incident_name?: string;
  description?: string;
  severity?: string;
  status?: string;
  creation_time?: string;
  detection_time?: string;
  last_update_time?: string;
  host_name?: string;
  user_name?: string;
  raw_response: any;
  alerts?: Array<{
    vendor_alert_id: string;
    alert_name?: string;
    severity?: string;
    detection_category?: string;
    status?: string;
    host_name?: string;
  }>;
}

export interface DashboardSummary {
  total_alerts: number;
  open_incidents: number;
  critical_high_alerts: number;
  severity_distribution: Record<string, number>;
  incident_status_distribution: Record<string, number>;
  alerts_over_time: Array<{ date: string; count: number }>;
  top_endpoints: Array<{ endpoint: string; count: number }>;
  top_detection_categories: Array<{ category: string; count: number }>;
  recent_alerts: Array<Alert>;
  recent_incidents: Array<Incident>;
  ai_executive_summary: any;
  last_sync_time?: string;
  sync_status: string;
  demo_mode: boolean;
}

export interface SyncStatus {
  configured: boolean;
  demo_mode: boolean;
  last_sync_time?: string;
  last_sync_entity?: string;
  last_job_status?: string;
  last_job_error?: string | null;
  connection_status: string;
}

export interface AISettings {
  provider: string;
  model: string;
  base_url?: string;
  enabled: boolean;
  demo_mode: boolean;
  prompt_version: string;
  temperature: number;
  max_tokens: number;
}

export interface AnalysisResult {
  summary: string;
  severity_assessment: string;
  confidence: number;
  observed_evidence: string[];
  potential_techniques: Array<{
    technique: string | null;
    tactic: string | null;
    confidence: number;
    evidence: string;
  }>;
  false_positive_considerations: string[];
  recommended_investigations: string[];
  recommended_actions: string[];
  evidence_references: Array<{
    alert_id: string | null;
    field: string | null;
    value: string | null;
  }>;
  limitations: string[];
  hypothesis_flags: string[];
}

export interface AnalyzeResponse {
  analysis_id: string;
  vendor_alert_id?: string;
  vendor_incident_id?: string;
  model_name: string;
  prompt_version: string;
  analysis_timestamp: string;
  result: AnalysisResult;
  is_demo: boolean;
  cached: boolean;
}

export function setToken(token: string) {
  localStorage.setItem("soc_token", token);
}
export function clearToken() {
  localStorage.removeItem("soc_token");
}
export function getToken() {
  return localStorage.getItem("soc_token");
}