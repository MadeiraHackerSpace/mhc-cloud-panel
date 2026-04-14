import { backendFetch } from "@/lib/api/backend";
import type { Page } from "@/lib/types/api";

type Customer = {
  id: string;
  tenant_id: string;
  display_name: string;
  email: string;
};

export default async function AdminCustomersPage() {
  const data = await backendFetch<Page<Customer>>("/api/v1/customers?limit=50&offset=0");

  return (
    <section className="rounded-xl border border-border bg-panel p-6">
      <h1 className="text-xl font-semibold">Clientes</h1>
      {data.items.length === 0 ? (
        <div className="mt-4 text-sm text-muted">Nenhum cliente.</div>
      ) : (
        <div className="mt-4 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg text-muted">
              <tr>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">E-mail</th>
                <th className="px-4 py-3">Tenant</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr key={c.id} className="border-t border-border">
                  <td className="px-4 py-3 font-medium">{c.display_name}</td>
                  <td className="px-4 py-3 text-muted">{c.email}</td>
                  <td className="px-4 py-3 text-muted">{c.tenant_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

