import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  AlertTriangle,
  ShieldAlert,
  Settings,
  LogOut,
  Menu,
  X,
  Globe,
} from "lucide-react";
import { useLang } from "../contexts/LanguageContext";
import { Link } from "react-router-dom";

const nav = [
  { href: "/", Icon: LayoutDashboard, key: "nav_dashboard" },
  { href: "/alerts", Icon: AlertTriangle, key: "nav_alerts" },
  { href: "/incidents", Icon: ShieldAlert, key: "nav_incidents" },
  { href: "/settings", Icon: Settings, key: "nav_settings" },
];

export function Sidebar() {
  const { lang, setLang, T, dir } = useLang();
  const [open, setOpen] = useState(dir === "ltr");
  const navigate = useNavigate();

  return (
    <aside className={`fixed inset-y-0 z-50 w-64 soc-panel border-r border-soc-border transform transition duration-300 ${
      open ? "translate-x-0" : "-translate-x-full"
    } ${dir === "rtl" ? "right-0 left-auto" : "left-0"}`}>
      <div className="flex items-center justify-between h-12 px-5">
        <span className="font-bold text-soc-accent tracking-tight">SOC</span>
        {dir === "rtl" && <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>}
      </div>
      <nav className="mt-4 px-3 space-y-1">
        {nav.map((item) => {
          const Icon = item.Icon;
          return (
            <Link
              key={item.key}
              to={item.href}
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition text-gray-400 hover:bg-white/5 hover:text-white"
            >
              <Icon className="w-5 h-5" />
              {T(item.key)}
            </Link>
          );
        })}
      </nav>
      <div className="absolute bottom-0 w-full border-t border-soc-border/50 p-4">
        <div className="flex items-center gap-3 px-2 mb-3">
          <Globe className="w-5 h-5 text-gray-400" />
          <button
            onClick={() => setLang(lang === "en" ? "ar" : "en")}
            className="flex items-center gap-2 w-full text-left text-sm text-gray-300 hover:text-white"
          >
            {lang === "en" ? "English" : "العربية"}
          </button>
        </div>
        <button
          onClick={() => navigate("/login")}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-red-400 hover:bg-red-900/20 transition"
        >
          <LogOut className="w-5 h-5" />
          {T("nav_logout")}
        </button>
      </div>
    </aside>
  );
};