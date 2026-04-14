import Link from "next/link";

export default function AdminHome() {
  return (
    <section className="rounded-xl border border-border bg-panel p-6">
      <h1 className="text-xl font-semibold">Admin</h1>
      <p className="mt-1 text-sm text-muted">Gestão de clientes, planos, infraestrutura e auditoria.</p>
      <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-2">
        <Link href="/admin/customers" className="rounded-md border border-border bg-bg px-4 py-3 text-sm">
          Clientes
        </Link>
        <Link href="/admin/plans" className="rounded-md border border-border bg-bg px-4 py-3 text-sm">
          Planos
        </Link>
        <Link href="/admin/infrastructure" className="rounded-md border border-border bg-bg px-4 py-3 text-sm">
          Infraestrutura Proxmox
        </Link>
        <Link href="/admin/jobs" className="rounded-md border border-border bg-bg px-4 py-3 text-sm">
          Jobs
        </Link>
        <Link href="/admin/audit" className="rounded-md border border-border bg-bg px-4 py-3 text-sm">
          Auditoria
        </Link>
      </div>
    </section>
  );
}

