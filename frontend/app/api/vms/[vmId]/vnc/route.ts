import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ vmId: string }> }
) {
  const { vmId } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value;

  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const apiUrl = process.env.API_BASE_URL || 'http://backend:8000';

  try {
    const res = await fetch(`${apiUrl}/api/v1/vms/${vmId}/vnc`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      const error = await res.json();
      return NextResponse.json(error, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('VNC proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to get VNC proxy' },
      { status: 500 }
    );
  }
}
