export type Role = 'admin' | 'analyst' | 'viewer';
export type User = { id: number; email: string; full_name: string; role: Role; created_at: string };
export type Asset = { id: number; tag: string; name: string; kind: string; status: string; assigned_to: string | null; location: string | null; created_at: string; updated_at: string };
export type Incident = { id: number; title: string; description: string; severity: string; status: string; asset_id: number | null; created_by_id: number; assigned_to: string | null; created_at: string; updated_at: string };
export type Audit = { id: number; actor_email: string; action: string; resource_type: string; resource_id: number; details: string; created_at: string };
export type Dashboard = { total_assets: number; active_assets: number; open_incidents: number; critical_incidents: number; recent_incidents: Incident[]; recent_audit: Audit[] };
export type LoginResponse = { access_token: string; token_type: string };

// Tokens are kept only in memory; refreshing the browser requires logging in again.
let token: string | null = null;
export function setToken(next: string | null) { token = next; }

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body);
    } catch { /* generic HTTP error */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const json = (body: unknown, method: 'POST' | 'PATCH' = 'POST'): RequestInit => ({ method, body: JSON.stringify(body) });
