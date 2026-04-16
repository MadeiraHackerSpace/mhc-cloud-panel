import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import VNCConsole from '@/components/VNCConsole';

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

  return (
    <div className="h-screen w-screen flex flex-col bg-black">
      <div className="bg-gray-900 text-white px-6 py-3 flex items-center justify-between border-b border-gray-800">
        <div className="flex items-center space-x-4">
          <a
            href={`/dashboard/vps/${id}`}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </a>
          <div>
            <h1 className="text-lg font-semibold">{vm.name}</h1>
            <p className="text-sm text-gray-400">Console VNC</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-400">
          <span>Node: {vm.proxmox_node}</span>
          <span>•</span>
          <span>VMID: {vm.proxmox_vmid}</span>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <VNCConsole vmId={id} proxmoxHost={proxmoxHost} />
      </div>
    </div>
  );
}
