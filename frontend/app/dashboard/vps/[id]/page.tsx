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
        <div className="mt-2 text-sm text-muted">
          Em breve: console web seguro via proxy no backend.
        </div>
      </section>
    </div>
  );
}

