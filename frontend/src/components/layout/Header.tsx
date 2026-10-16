import { useState } from "react";
import { Menu, Sun, Moon, Bell } from "lucide-react";
import { useLang } from "../contexts/LanguageContext";

export function Header() => {
  const { T, dir } = useLang();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 soc-panel border-b border-soc-border bg-soc-panel/95 backdrop-blur">
      <div className="flex items-center justify-between h-14 px-5">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileOpen((p) => !p)}
            className="md:hidden text-gray-400 hover:text-white"
            aria-label="Toggle menu"
          >
            <Menu className="w-6 h-6" />
          </button>
          <span className="font-bold text-soc-accent tracking-tight">SOC Dashboard</span>
        </div>
        <div className="flex items-center gap-3 md:gap-4">
          <div className="hidden md:flex items-center gap-2">
            <button
              onClick={() => (document.documentElement.classList.toggle("dark"))}
              className="text-gray-400 hover:text-white p-2 rounded hover:bg-white/5"
              aria-label="Theme"
            >
              {document.documentElement.classList.contains("dark") ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <button className="text-gray-400 hover:text-white relative p-2 rounded hover:bg-white/5" aria-label="Notifications">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>
          </div>
          <span className="hidden md:block text-xs text-gray-500">API · /api/docs</span>
        </div>
      </div>
    </header>
  );
};