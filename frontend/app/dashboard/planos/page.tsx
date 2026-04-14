import { backendFetch } from "@/lib/api/backend";
import type { Page, Plan } from "@/lib/types/api";
import { ContractPlan } from "@/components/contract-plan";

export default async function PlansPage() {
  const data = await backendFetch<Page<Plan>>("/api/v1/plans?limit=50&offset=0&active_only=true");

  return (
    <section className="space-y-4">
      <div className="rounded-xl border border-border bg-panel p-6">
        <h1 className="text-xl font-semibold">Planos</h1>
        <p className="mt-1 text-sm text-muted">Planos padronizados para membros do MHC.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {data.items.map((p) => (
          <div key={p.id} className="rounded-xl border border-border bg-panel p-6">
            <div className="text-base font-semibold">{p.name}</div>
            <div className="mt-2 text-2xl font-semibold">
              R$ {p.price_monthly} <span className="text-sm font-normal text-muted">/ mês</span>
            </div>
            <ul className="mt-4 space-y-1 text-sm text-muted">
              <li>{p.vcpu} vCPU</li>
              <li>{Math.round(p.ram_mb / 1024)} GB RAM</li>
              <li>{p.disk_gb} GB SSD</li>
              <li>{p.traffic_gb} GB tráfego</li>
              <li>{p.ipv4_count} IPv4</li>
            </ul>
            <div className="mt-5">
              <ContractPlan planId={p.id} planName={p.name} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

