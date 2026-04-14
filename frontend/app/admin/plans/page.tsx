import { backendFetch } from "@/lib/api/backend";
import type { Page, Plan } from "@/lib/types/api";

export default async function AdminPlansPage() {
  const data = await backendFetch<Page<Plan>>("/api/v1/plans?limit=50&offset=0&active_only=false");

  return (
    <section className="rounded-xl border border-border bg-panel p-6">
      <h1 className="text-xl font-semibold">Planos</h1>
      <div className="mt-4 overflow-hidden rounded-lg border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-bg text-muted">
            <tr>
              <th className="px-4 py-3">Nome</th>
              <th className="px-4 py-3">Preço mensal</th>
              <th className="px-4 py-3">vCPU</th>
              <th className="px-4 py-3">RAM</th>
              <th className="px-4 py-3">Disco</th>
              <th className="px-4 py-3">Ativo</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((p) => (
              <tr key={p.id} className="border-t border-border">
                <td className="px-4 py-3 font-medium">{p.name}</td>
                <td className="px-4 py-3 text-muted">R$ {p.price_monthly}</td>
                <td className="px-4 py-3 text-muted">{p.vcpu}</td>
                <td className="px-4 py-3 text-muted">{Math.round(p.ram_mb / 1024)} GB</td>
                <td className="px-4 py-3 text-muted">{p.disk_gb} GB</td>
                <td className="px-4 py-3 text-muted">{p.is_active ? "Sim" : "Não"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

