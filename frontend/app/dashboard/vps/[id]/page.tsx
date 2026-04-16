import Link from "next/link";
import { backendFetch } from "@/lib/api/backend";
import type { VM } from "@/lib/types/api";
import { VMActionButtons } from "@/components/vm-actions";

export default async function VPSDetailPage({ params }: { params: { id: string } }) {
  const vm = await backendFetch<VM>(`/api/v1/vms/${params.id}`);
  const status = await backendFetch<{ ok: boolean; status: Record<string, unknown> }>(
    `/api/v1/vms/${params.id}/status`
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/dashboard/vps" className="text-sm text-brand">
          Voltar
        </Link>
      </div>

      <section className="rounded-xl border border-border bg-panel p-6">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-xl font-semibold">{vm.name}</h1>
            <div className="mt-1 text-sm text-muted">
              Status: {vm.status} • Node: {vm.proxmox_node} • VMID: {vm.proxmox_vmid}
            </div>
          </div>
          <VMActionButtons vmId={vm.id} />
        </div>
      </section>

      <section className="rounded-xl border border-border bg-panel p-6">
        <h2 className="text-base font-semibold">Uso / Status (Proxmox)</h2>
        <pre className="mt-4 overflow-x-auto rounded-lg border border-border bg-bg p-4 text-xs text-muted">
          {JSON.stringify(status.status, null, 2)}
        </pre>
      </section>

      <section className="rounded-xl border border-border bg-panel p-6">
        <h2 className="text-base font-semibold">Console</h2>
        <div className="mt-4 flex items-center gap-4">
          <Link
            href={`/dashboard/vps/${params.id}/console`}
            className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand/90 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Abrir Console VNC
          </Link>
          <p className="text-sm text-muted">
            Acesse o console gráfico da VM diretamente no navegador
          </p>
        </div>
      </section>
    </div>
  );
}

