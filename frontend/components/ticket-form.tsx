"use client";

import { useState } from "react";

export function TicketForm() {
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setOk(false);
    const res = await fetch("/api/tickets", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ subject, priority: "normal", message })
    });
    const data = await res.json().catch(() => null);
    setLoading(false);
    if (!res.ok) {
      setError(data?.error?.message || "Falha ao abrir ticket");
      return;
    }
    setSubject("");
    setMessage("");
    setOk(true);
    window.location.reload();
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="space-y-1">
        <label className="text-sm">Assunto</label>
        <input
          className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm">Mensagem</label>
        <textarea
          className="min-h-[120px] w-full rounded-md border border-border bg-bg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          required
        />
      </div>
      {error ? <div className="text-sm text-muted">{error}</div> : null}
      {ok ? <div className="text-sm text-muted">Ticket aberto.</div> : null}
      <button
        disabled={loading}
        type="submit"
        className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {loading ? "Enviando..." : "Abrir ticket"}
      </button>
    </form>
  );
}

