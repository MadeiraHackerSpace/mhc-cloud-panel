"use client";

import { useState } from "react";

export function LoginForm({ nextPath }: { nextPath: string }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      credentials: "include",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json().catch(() => null);
    setLoading(false);
    if (!res.ok) {
      setError(data?.error?.message || "Não foi possível autenticar");
      return;
    }
    window.location.assign(nextPath);
  }

  return (
    <div className="mx-auto max-w-md rounded-xl border border-border bg-panel p-6">
      <h1 className="text-xl font-semibold">Entrar</h1>
      <p className="mt-1 text-sm text-muted">Use suas credenciais para acessar o painel.</p>

      <form className="mt-6 space-y-4" onSubmit={onSubmit}>
        <div className="space-y-1">
          <label className="text-sm">E-mail</label>
          <input
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            autoComplete="email"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm">Senha</label>
          <input
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete="current-password"
            required
          />
        </div>

        {error ? (
          <div className="rounded-md border border-border bg-bg p-3 text-sm text-muted">{error}</div>
        ) : null}

        <button
          disabled={loading}
          className="w-full rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          type="submit"
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>

      <div className="mt-6 text-xs text-muted">
        Demo: superadmin@mhc.local / admin12345 • cliente@mhc.local / admin12345
      </div>
    </div>
  );
}

