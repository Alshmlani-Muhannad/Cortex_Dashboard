import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLang } from "../contexts/LanguageContext";
import { api, setToken } from "../lib/api";
import { Button, Input } from "../components/ui";
import { AlertTriangle, Lock, LogIn } from "lucide-react";

export default function Login() {
  const { T, lang, dir } = useLang();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/auth/login", { username, password });
      setToken(res.data.access_token);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || T("error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center ${dir === "rtl" ? "rtl" : ""}`}>
      <div className="soc-panel w-full max-w-md p-8">
        <div className="mb-6 flex items-center gap-2">
          <LogIn className="w-6 h-6 text-soc-accent" />
          <h1 className="text-xl font-bold">{T("app_name")}</h1>
        </div>
        <p className="text-gray-400 text-sm mb-6">{T("sign_in")}</p>
        {error && (
          <div className="mb-4 p-3 rounded bg-red-900/20 border border-red-900/30 text-red-400 text-sm">
            <AlertTriangle className="w-4 h-4 mr-2" /> {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">{T("username")}</label>
            <Input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="admin" required />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{T("password")}</label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <Button type="submit" variant="primary" className="w-full" disabled={loading}>
            <Lock className="w-4 h-4 mr-2" /> {loading ? T("loading") : T("sign_in_button")}
          </Button>
        </form>
        <p className="mt-6 text-xs text-gray-500 text-center">
          Default: admin / admin123 (local dev only)
        </p>
      </div>
    </div>
  );
}