import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 px-6 py-10">
      <header className="flex items-center justify-between">
        <div className="text-lg font-semibold">MHC Cloud Panel</div>
        <ThemeToggle />
      </header>

      <section className="rounded-xl border border-border bg-panel p-8">
        <h1 className="text-3xl font-semibold">Revenda e gestão de VPS</h1>
        <p className="mt-3 text-muted">
          Plataforma SaaS multi-tenant integrada ao Proxmox VE, com portal do cliente e painel administrativo.
        </p>
        <div className="mt-6 flex gap-3">
          <Link
            href="/login"
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white"
          >
            Entrar
          </Link>
          <Link
            href="/dashboard"
            className="rounded-md border border-border bg-panel px-4 py-2 text-sm font-medium"
          >
            Ir para o painel
          </Link>
        </div>
      </section>
    </main>
  );
}

