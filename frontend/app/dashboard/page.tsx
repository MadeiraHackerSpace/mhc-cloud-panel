import Link from "next/link";
import { backendFetch } from "@/lib/api/backend";
import type { Page, Service, VM } from "@/lib/types/api";

export default async function DashboardPage() {
  const services = await backendFetch<Page<Service>>("/api/v1/services?limit=5&offset=0");
  const vms = await backendFetch<Page<VM>>("/api/v1/vms?limit=5&offset=0");

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-border bg-panel p-6">
        <h1 className="text-xl font-semibold">Visão geral</h1>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-border bg-bg p-4">
            <div className="text-sm text-muted">Serviços</div>
            <div className="mt-1 text-2xl font-semibold">{services.meta.total}</div>
          </div>
          <div className="rounded-lg border border-border bg-bg p-4">
            <div className="text-sm text-muted">VPS</div>
            <div className="mt-1 text-2xl font-semibold">{vms.meta.total}</div>
          </div>
          <div className="rounded-lg border border-border bg-bg p-4">
            <div className="text-sm text-muted">Status</div>
            <div className="mt-1 text-sm text-muted">Provisionamento assíncrono e auditoria habilitados</div>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-panel p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Últimas VPS</h2>
          <Link href="/dashboard/vps" className="text-sm text-brand">
            Ver todas
          </Link>
        </div>
        {vms.items.length === 0 ? (
          <div className="mt-4 text-sm text-muted">Nenhuma VPS ainda.</div>
        ) : (
          <div className="mt-4 space-y-2">
            {vms.items.map((vm) => (
              <Link
                key={vm.id}
                href={`/dashboard/vps/${vm.id}`}
                className="flex items-center justify-between rounded-md border border-border bg-bg px-4 py-3 text-sm hover:opacity-90"
              >
                <div className="font-medium">{vm.name}</div>
                <div className="text-muted">{vm.status}</div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

