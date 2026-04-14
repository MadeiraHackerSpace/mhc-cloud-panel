import Link from "next/link";
import { backendFetch } from "@/lib/api/backend";
import type { Page, VM } from "@/lib/types/api";

export default async function VPSListPage() {
  const data = await backendFetch<Page<VM>>("/api/v1/vms?limit=50&offset=0");

  return (
    <section className="rounded-xl border border-border bg-panel p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">VPS</h1>
        <Link href="/dashboard/planos" className="text-sm text-brand">
          Contratar plano
        </Link>
      </div>

      {data.items.length === 0 ? (
        <div className="mt-4 text-sm text-muted">Nenhuma VPS encontrada.</div>
      ) : (
        <div className="mt-4 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg text-muted">
              <tr>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Node</th>
                <th className="px-4 py-3">VMID</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((vm) => (
                <tr key={vm.id} className="border-t border-border">
                  <td className="px-4 py-3">
                    <Link href={`/dashboard/vps/${vm.id}`} className="font-medium hover:underline">
                      {vm.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted">{vm.status}</td>
                  <td className="px-4 py-3 text-muted">{vm.proxmox_node}</td>
                  <td className="px-4 py-3 text-muted">{vm.proxmox_vmid}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

