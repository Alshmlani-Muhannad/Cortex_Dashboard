import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { TRANSLATIONS, t, Lang } from "../i18n";

const LanguageContext = createContext<{
  lang: Lang;
  setLang: (lang: Lang) => void;
  T: (key: string) => string;
  dir: "ltr" | "rtl";
} | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const stored = localStorage.getItem("soc_lang") as Lang;
    return stored === "ar" ? "ar" : "en";
  });

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    localStorage.setItem("soc_lang", next);
    document.documentElement.dir = next === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = next;
  }, []);

  useEffect(() => {
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = lang;
  }, [lang]);

  const T = useCallback((key: string) => t(lang, key), [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, T, dir: lang === "ar" ? "rtl" : "ltr" }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLang() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLang must be used within LanguageProvider");
  return ctx;
}