export type PageMeta = {
  limit: number;
  offset: number;
  total: number;
};

export type Page<T> = {
  meta: PageMeta;
  items: T[];
};

export type User = {
  id: string;
  tenant_id: string | null;
  role_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
};

export type Plan = {
  id: string;
  name: string;
  price_monthly: string;
  price_quarterly: string | null;
  vcpu: number;
  ram_mb: number;
  disk_gb: number;
  traffic_gb: number;
  ipv4_count: number;
  ipv6_enabled: boolean;
  snapshots_enabled: boolean;
  backups_enabled: boolean;
  upgrade_downgrade_allowed: boolean;
  is_active: boolean;
};

export type Service = {
  id: string;
  name: string;
  status: string;
  billing_cycle: string;
  plan_id: string;
  created_at?: string;
};

export type VM = {
  id: string;
  service_id: string;
  name: string;
  status: string;
  proxmox_node: string;
  proxmox_vmid: number;
  primary_ipv4: string | null;
};

export type Invoice = {
  id: string;
  number: string;
  status: string;
  amount_total: string;
  due_date: string;
  paid_at: string | null;
};

export type Ticket = {
  id: string;
  subject: string;
  status: string;
  priority: string;
  last_message_at: string | null;
};

