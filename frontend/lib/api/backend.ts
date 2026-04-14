import { cookies } from "next/headers";

function demoResponse(path: string): unknown {
  const url = new URL(path, "http://local");

  if (url.pathname === "/api/v1/plans") {
    return {
      meta: { limit: 50, offset: 0, total: 3 },
      items: [
        {
          id: "plan-bronze",
          name: "Bronze",
          price_monthly: "29.90",
          price_quarterly: "79.90",
          vcpu: 1,
          ram_mb: 1024,
          disk_gb: 25,
          traffic_gb: 500,
          ipv4_count: 1,
          ipv6_enabled: true,
          snapshots_enabled: false,
          backups_enabled: false,
          upgrade_downgrade_allowed: true,
          is_active: true
        },
        {
          id: "plan-silver",
          name: "Silver",
          price_monthly: "49.90",
          price_quarterly: "139.90",
          vcpu: 2,
          ram_mb: 2048,
          disk_gb: 50,
          traffic_gb: 1000,
          ipv4_count: 1,
          ipv6_enabled: true,
          snapshots_enabled: false,
          backups_enabled: false,
          upgrade_downgrade_allowed: true,
          is_active: true
        },
        {
          id: "plan-gold",
          name: "Gold",
          price_monthly: "89.90",
          price_quarterly: "249.90",
          vcpu: 4,
          ram_mb: 4096,
          disk_gb: 100,
          traffic_gb: 2000,
          ipv4_count: 1,
          ipv6_enabled: true,
          snapshots_enabled: false,
          backups_enabled: false,
          upgrade_downgrade_allowed: true,
          is_active: true
        }
      ]
    };
  }

  if (url.pathname === "/api/v1/services") {
    return {
      meta: { limit: 20, offset: 0, total: 1 },
      items: [
        {
          id: "svc-demo",
          tenant_id: "tenant-demo",
          customer_id: "cust-demo",
          plan_id: "plan-silver",
          name: "VPS Demo",
          status: "active",
          billing_cycle: "monthly",
          started_at: new Date().toISOString(),
          suspended_at: null,
          cancelled_at: null,
          pending_removal_at: null,
          grace_period_ends_at: null
        }
      ]
    };
  }

  if (url.pathname === "/api/v1/vms") {
    return {
      meta: { limit: 20, offset: 0, total: 1 },
      items: [
        {
          id: "vm-demo",
          tenant_id: "tenant-demo",
          service_id: "svc-demo",
          proxmox_node: "pve",
          proxmox_vmid: 110,
          name: "VPS Demo",
          status: "running",
          primary_ipv4: "192.0.2.10",
          primary_ipv6: null,
          template_id: null,
          last_synced_at: new Date().toISOString()
        }
      ]
    };
  }

  if (url.pathname.startsWith("/api/v1/vms/") && url.pathname.endsWith("/status")) {
    return { ok: true, status: { status: "running", cpu: 0, mem: 0 } };
  }

  if (url.pathname.startsWith("/api/v1/vms/")) {
    return {
      id: "vm-demo",
      tenant_id: "tenant-demo",
      service_id: "svc-demo",
      proxmox_node: "pve",
      proxmox_vmid: 110,
      name: "VPS Demo",
      status: "running",
      primary_ipv4: "192.0.2.10",
      primary_ipv6: null,
      template_id: null,
      last_synced_at: new Date().toISOString()
    };
  }

  if (url.pathname === "/api/v1/invoices") {
    return {
      meta: { limit: 50, offset: 0, total: 2 },
      items: [
        {
          id: "inv-1",
          tenant_id: "tenant-demo",
          customer_id: "cust-demo",
          service_id: "svc-demo",
          number: "INV-DEMO-001",
          status: "paid",
          currency: "BRL",
          amount_total: "49.90",
          due_date: new Date(Date.now() - 86400000).toISOString(),
          paid_at: new Date(Date.now() - 3600000).toISOString()
        },
        {
          id: "inv-2",
          tenant_id: "tenant-demo",
          customer_id: "cust-demo",
          service_id: "svc-demo",
          number: "INV-DEMO-002",
          status: "open",
          currency: "BRL",
          amount_total: "49.90",
          due_date: new Date(Date.now() + 86400000 * 3).toISOString(),
          paid_at: null
        }
      ]
    };
  }

  if (url.pathname === "/api/v1/tickets") {
    return { meta: { limit: 50, offset: 0, total: 0 }, items: [] };
  }

  if (url.pathname === "/api/v1/admin/proxmox/nodes") {
    return [{ node: "pve", status: "online", maxcpu: 16, maxmem: 34359738368, mem: 2147483648 }];
  }

  if (url.pathname === "/api/v1/admin/jobs") {
    return { meta: { limit: 50, offset: 0, total: 0 }, items: [] };
  }

  if (url.pathname === "/api/v1/admin/audit") {
    return { meta: { limit: 50, offset: 0, total: 0 }, items: [] };
  }

  return { meta: { limit: 20, offset: 0, total: 0 }, items: [] };
}

export async function backendFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const jar = cookies();
  const demo =
    jar.get("mhc_demo")?.value === "1" ||
    jar.get("mhc_access_token")?.value === "demo" ||
    process.env.MHC_FORCE_DEMO === "true";
  if (demo) return demoResponse(path) as T;

  const base =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000";
  const access = jar.get("mhc_access_token")?.value;

  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(access ? { authorization: `Bearer ${access}` } : {}),
      ...(init?.headers || {})
    },
    cache: "no-store"
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}
