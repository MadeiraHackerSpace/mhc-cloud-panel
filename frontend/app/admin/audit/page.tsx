import { backendFetch } from "@/lib/api/backend";
import type { Page } from "@/lib/types/api";

type AuditLog = {
  id: string;
  action: string;
  entity: string;
  entity_id: string | null;
  success: boolean;
  created_at: string;
};

export default async function AdminAuditPage() {
  const data = await backendFetch<Page<AuditLog>>("/api/v1/admin/audit?limit=50&offset=0");

  return (
    <section className="rounded-xl border border-border bg-panel p-6">
      <h1 className="text-xl font-semibold">Auditoria</h1>
      {data.items.length === 0 ? (
        <div className="mt-4 text-sm text-muted">Nenhum evento.</div>
      ) : (
        <div className="mt-4 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg text-muted">
              <tr>
                <th className="px-4 py-3">Ação</th>
                <th className="px-4 py-3">Entidade</th>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Ok</th>
                <th className="px-4 py-3">Data</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((a) => (
                <tr key={a.id} className="border-t border-border">
                  <td className="px-4 py-3 font-medium">{a.action}</td>
                  <td className="px-4 py-3 text-muted">{a.entity}</td>
                  <td className="px-4 py-3 text-muted">{a.entity_id || "-"}</td>
                  <td className="px-4 py-3 text-muted">{a.success ? "Sim" : "Não"}</td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(a.created_at).toLocaleString("pt-BR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

