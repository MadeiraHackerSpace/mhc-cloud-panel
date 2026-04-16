import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

interface PageProps {
  params: Promise<{ id: string }>;
}

async function getVM(id: string, token: string) {
  const apiUrl = process.env.API_BASE_URL || 'http://backend:8000';
  const res = await fetch(`${apiUrl}/api/v1/vms/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: 'no-store',
  });

  if (!res.ok) {
    return null;
  }

  return res.json();
}

export default async function ConsolePage({ params }: PageProps) {
  const { id } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value;

  if (!token) {
    redirect('/login');
  }

  const vm = await getVM(id, token);

  if (!vm) {
    redirect('/dashboard/vps');
  }

  const proxmoxHost = process.env.NEXT_PUBLIC_PROXMOX_HOST || 'localhost';
  
  // Redirect to static VNC page with query params
  const vncUrl = `/vnc.html?vmId=${id}&vmName=${encodeURIComponent(vm.name)}&vmNode=${vm.proxmox_node}&vmVmid=${vm.proxmox_vmid}&proxmoxHost=${proxmoxHost}`;
  
  redirect(vncUrl);
}
