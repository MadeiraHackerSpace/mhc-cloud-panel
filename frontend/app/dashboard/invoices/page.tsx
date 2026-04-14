import { backendFetch } from "@/lib/api/backend";
import type { Invoice, Page } from "@/lib/types/api";

export default async function InvoicesPage() {
  const data = await backendFetch<Page<Invoice>>("/api/v1/invoices?limit=50&offset=0");

  return (
    <section className="rounded-xl border border-border bg-panel p-6">
      <h1 className="text-xl font-semibold">Faturas</h1>
      {data.items.length === 0 ? (
        <div className="mt-4 text-sm text-muted">Nenhuma fatura.</div>
      ) : (
        <div className="mt-4 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg text-muted">
              <tr>
                <th className="px-4 py-3">Número</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Valor</th>
                <th className="px-4 py-3">Vencimento</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((inv) => (
                <tr key={inv.id} className="border-t border-border">
                  <td className="px-4 py-3 font-medium">{inv.number}</td>
                  <td className="px-4 py-3 text-muted">{inv.status}</td>
                  <td className="px-4 py-3 text-muted">R$ {inv.amount_total}</td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(inv.due_date).toLocaleDateString("pt-BR")}
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

