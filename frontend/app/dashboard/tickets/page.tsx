import { backendFetch } from "@/lib/api/backend";
import type { Page, Ticket } from "@/lib/types/api";
import { TicketForm } from "@/components/ticket-form";

export default async function TicketsPage() {
  const data = await backendFetch<Page<Ticket>>("/api/v1/tickets?limit=50&offset=0");

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-border bg-panel p-6">
        <h1 className="text-xl font-semibold">Tickets</h1>
        <p className="mt-1 text-sm text-muted">Abra e acompanhe solicitações de suporte.</p>
      </section>

      <section className="rounded-xl border border-border bg-panel p-6">
        <h2 className="text-base font-semibold">Abrir ticket</h2>
        <div className="mt-4">
          <TicketForm />
        </div>
      </section>

      <section className="rounded-xl border border-border bg-panel p-6">
        <h2 className="text-base font-semibold">Meus tickets</h2>
        {data.items.length === 0 ? (
          <div className="mt-4 text-sm text-muted">Nenhum ticket.</div>
        ) : (
          <div className="mt-4 space-y-2">
            {data.items.map((t) => (
              <div key={t.id} className="rounded-md border border-border bg-bg px-4 py-3 text-sm">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{t.subject}</div>
                  <div className="text-muted">{t.status}</div>
                </div>
                <div className="mt-1 text-xs text-muted">Prioridade: {t.priority}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

