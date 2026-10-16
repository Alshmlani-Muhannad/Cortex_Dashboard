import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

export function AppLayout() {
  const location = useLocation();
  return (
    <div className="min-h-screen bg-soc-dark">
      <Sidebar />
      <div className={`md:ml-64 ${typeof document !== "undefined" && document.documentElement.dir === "rtl" ? "md:mr-64 md:ml-0" : ""}`}>
        <Header />
        <main className="p-5">
          <Outlet context={{ location }} />
        </main>
      </div>
    </div>
  );
}