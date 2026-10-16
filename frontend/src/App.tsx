import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { useLang } from "./contexts/LanguageContext";
import { getToken } from "./lib/api";

function Protected({ children }: { children: React.ReactNode }) {
  const token = getToken();
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

const Login = React.lazy(() => import("./pages/Login"));
const Dashboard = React.lazy(() => import("./pages/Dashboard"));
const Alerts = React.lazy(() => import("./pages/Alerts"));
const AlertDetail = React.lazy(() => import("./pages/AlertDetail"));
const Incidents = React.lazy(() => import("./pages/Incidents"));
const IncidentDetail = React.lazy(() => import("./pages/IncidentDetail"));
const Settings = React.lazy(() => import("./pages/Settings"));

export default function App() {
  const { T } = useLang();
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <>
            <Protected>
              <AppLayout />
            </Protected>
          </>
        }
      >
        <Route index element={<Navigate to="/" replace />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="alerts/:alertId" element={<AlertDetail />} />
        <Route path="incidents" element={<Incidents />} />
        <Route path="incidents/:incidentId" element={<IncidentDetail />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}