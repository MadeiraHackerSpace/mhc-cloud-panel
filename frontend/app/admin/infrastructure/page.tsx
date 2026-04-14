import { backendFetch } from "@/lib/api/backend";

type ProxmoxNodeInfo = {
  node: string;
  status?: string | null;
  maxcpu?: number | null;
  maxmem?: number | null;
  mem?: number | null;
};

export default async function AdminInfrastructurePage() {
  const nodes = await backendFetch<ProxmoxNodeInfo[]>("/api/v1/admin/proxmox/nodes");

  return (
    <section className="rounded-xl border border-border bg-panel p-6">
      <h1 className="text-xl font-semibold">Infraestrutura (Proxmox)</h1>
      <p className="mt-1 text-sm text-muted">Consulta via API com token (backend only).</p>

      {nodes.length === 0 ? (
        <div className="mt-4 text-sm text-muted">Nenhum node retornado.</div>
      ) : (
        <div className="mt-4 space-y-2">
          {nodes.map((n) => (
            <div key={n.node} className="rounded-md border border-border bg-bg px-4 py-3 text-sm">
              <div className="font-medium">{n.node}</div>
              <div className="mt-1 text-xs text-muted">
                status: {n.status || "-"} • cpu: {n.maxcpu ?? "-"} • mem: {n.mem ?? "-"} / {n.maxmem ?? "-"}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

