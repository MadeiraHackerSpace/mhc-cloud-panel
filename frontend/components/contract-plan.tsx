"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function ContractPlan({ planId, planName }: { planId: string; planName: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function contract() {
    setLoading(true);
    setError(null);
    const now = new Date();
    const pad2 = (n: number) => String(n).padStart(2, "0");
    const stamp = `${now.getFullYear()}${pad2(now.getMonth() + 1)}${pad2(now.getDate())}-${pad2(now.getHours())}${pad2(now.getMinutes())}${pad2(now.getSeconds())}`;
    const safePlan =
      planName
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 24) || "plano";
    const name = `portal-${safePlan}-${stamp}`;
    const res = await fetch("/api/services/contract", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ plan_id: planId, name, billing_cycle: "monthly", confirm: true })
    });
    const data = await res.json().catch(() => null);
    setLoading(false);
    if (!res.ok) {
      setError(data?.error?.message || "Falha ao contratar");
      return;
    }
    router.replace("/dashboard");
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={contract}
        disabled={loading}
        className="w-full rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {loading ? "Contratando..." : "Contratar"}
      </button>
      {error ? <div className="text-xs text-muted">{error}</div> : null}
    </div>
  );
}
