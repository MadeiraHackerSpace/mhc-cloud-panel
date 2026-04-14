import type { ReactNode } from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { LogoutButton } from "@/components/logout-button";

const nav = [
  { href: "/admin", label: "Resumo" },
  { href: "/admin/customers", label: "Clientes" },
  { href: "/admin/plans", label: "Planos" },
  { href: "/admin/infrastructure", label: "Infraestrutura" },
  { href: "/admin/jobs", label: "Jobs" },
  { href: "/admin/audit", label: "Auditoria" }
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-panel">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/admin" className="text-lg font-semibold">
            MHC Cloud Panel • Admin
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <LogoutButton />
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 px-6 py-6 md:grid-cols-[240px_1fr]">
        <aside className="rounded-xl border border-border bg-panel p-4">
          <nav className="space-y-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block rounded-md px-3 py-2 text-sm text-text hover:bg-bg"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-4">
            <Link href="/dashboard" className="text-sm text-brand">
              Voltar ao portal
            </Link>
          </div>
        </aside>
        <main>{children}</main>
      </div>
    </div>
  );
}

