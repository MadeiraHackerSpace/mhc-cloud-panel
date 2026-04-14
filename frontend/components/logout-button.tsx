"use client";

import { useRouter } from "next/navigation";

export function LogoutButton() {
  const router = useRouter();

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
  }

  return (
    <button
      type="button"
      onClick={logout}
      className="rounded-md border border-border bg-panel px-3 py-2 text-sm text-text hover:opacity-90"
    >
      Sair
    </button>
  );
}

