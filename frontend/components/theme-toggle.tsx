"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button
        type="button"
        className="rounded-md border border-border bg-panel px-3 py-2 text-sm text-text hover:opacity-90"
        aria-label="Alternar tema"
        disabled
      >
        Tema
      </button>
    );
  }
  const next = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      className="rounded-md border border-border bg-panel px-3 py-2 text-sm text-text hover:opacity-90"
      aria-label="Alternar tema"
    >
      {theme === "dark" ? "Tema claro" : "Tema escuro"}
    </button>
  );
}
