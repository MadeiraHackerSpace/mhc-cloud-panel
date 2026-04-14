"use client";

import { useState } from "react";

export function VMActionButtons({ vmId }: { vmId: string }) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(action: "start" | "stop" | "reboot") {
    setLoading(action);
    setError(null);
    try {
      await fetch(`/api/vms/${vmId}/${action}`, { method: "POST" });
      window.location.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-md bg-brand px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
          onClick={() => run("start")}
          disabled={loading !== null}
        >
          {loading === "start" ? "Iniciando..." : "Ligar"}
        </button>
        <button
          type="button"
          className="rounded-md border border-border bg-panel px-3 py-2 text-sm disabled:opacity-60"
          onClick={() => run("stop")}
          disabled={loading !== null}
        >
          {loading === "stop" ? "Parando..." : "Desligar"}
        </button>
        <button
          type="button"
          className="rounded-md border border-border bg-panel px-3 py-2 text-sm disabled:opacity-60"
          onClick={() => run("reboot")}
          disabled={loading !== null}
        >
          {loading === "reboot" ? "Reiniciando..." : "Reiniciar"}
        </button>
      </div>
      {error ? <div className="text-sm text-muted">{error}</div> : null}
    </div>
  );
}
