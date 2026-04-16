'use client';

import { useEffect, useRef, useState } from 'react';

interface VNCConsoleProps {
  vmId: string;
  proxmoxHost: string;
}

interface VNCProxyData {
  ticket: string;
  port: number;
  upid: string;
}

export default function VNCConsole({ vmId, proxmoxHost }: VNCConsoleProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const rfbRef = useRef<any>(null);
  const [status, setStatus] = useState<'loading' | 'connected' | 'disconnected' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let rfb: any = null;
    let mounted = true;

    async function initVNC() {
      try {
        setStatus('loading');
        setError(null);

        // Fetch VNC proxy credentials
        const response = await fetch(`/api/vms/${vmId}/vnc`, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`Failed to get VNC proxy: ${response.statusText}`);
        }

        const data: VNCProxyData = await response.json();

        if (!mounted) return;

        // Dynamically import noVNC only on client side
        const RFBModule = await import('@novnc/novnc/core/rfb.js');
        const RFB = RFBModule.default;

        if (!canvasRef.current || !mounted) {
          return;
        }

        // Build WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${proxmoxHost}:${data.port}/?vncticket=${encodeURIComponent(data.ticket)}`;

        // Initialize noVNC
        rfb = new RFB(canvasRef.current, wsUrl, {
          credentials: { password: data.ticket },
        });

        rfb.scaleViewport = true;
        rfb.resizeSession = true;

        rfb.addEventListener('connect', () => {
          if (mounted) setStatus('connected');
        });

        rfb.addEventListener('disconnect', () => {
          if (mounted) setStatus('disconnected');
        });

        rfb.addEventListener('securityfailure', (e: any) => {
          if (mounted) {
            setStatus('error');
            setError(`Security failure: ${e.detail.reason}`);
          }
        });

        rfbRef.current = rfb;
      } catch (err) {
        if (mounted) {
          setStatus('error');
          setError(err instanceof Error ? err.message : 'Unknown error');
          console.error('VNC initialization error:', err);
        }
      }
    }

    initVNC();

    return () => {
      mounted = false;
      if (rfbRef.current) {
        try {
          rfbRef.current.disconnect();
        } catch (e) {
          // Ignore disconnect errors
        }
        rfbRef.current = null;
      }
    };
  }, [vmId, proxmoxHost]);

  return (
    <div className="flex flex-col h-full w-full bg-black">
      {status === 'loading' && (
        <div className="flex items-center justify-center h-full">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p>Conectando ao console...</p>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="flex items-center justify-center h-full">
          <div className="text-red-400 text-center max-w-md">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="font-semibold mb-2">Erro ao conectar</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {status === 'disconnected' && (
        <div className="flex items-center justify-center h-full">
          <div className="text-gray-400 text-center">
            <p>Desconectado do console</p>
          </div>
        </div>
      )}

      <div
        ref={canvasRef}
        className="flex-1 w-full"
        style={{ display: status === 'connected' ? 'block' : 'none' }}
      />

      {status === 'connected' && (
        <div className="bg-gray-900 text-white text-xs px-4 py-2 flex items-center justify-between">
          <span className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
            Conectado
          </span>
          <span className="text-gray-400">
            Use Ctrl+Alt+Del: Enviar via menu do navegador
          </span>
        </div>
      )}
    </div>
  );
}
