import { backendFetch } from "@/lib/api/backend";
import type { Page } from "@/lib/types/api";

type Job = {
  id: string;
  job_type: string;
  status: string;
  created_at?: string;
  error_message?: string | null;
};

export default async function AdminJobsPage() {
  const data = await backendFetch<Page<Job>>("/api/v1/admin/jobs?limit=50&offset=0");

  return (
    <section className="rounded-xl border border-border bg-panel p-6">
      <h1 className="text-xl font-semibold">Jobs</h1>
      {data.items.length === 0 ? (
        <div className="mt-4 text-sm text-muted">Nenhum job.</div>
      ) : (
        <div className="mt-4 space-y-2">
          {data.items.map((j) => (
            <div key={j.id} className="rounded-md border border-border bg-bg px-4 py-3 text-sm">
              <div className="flex items-center justify-between">
                <div className="font-medium">{j.job_type}</div>
                <div className="text-muted">{j.status}</div>
              </div>
              {j.error_message ? <div className="mt-1 text-xs text-muted">{j.error_message}</div> : null}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

