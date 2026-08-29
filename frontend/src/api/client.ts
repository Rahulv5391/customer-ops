const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000/api/v1';

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('ops_token');
  const customHeaders = (options?.headers ?? {}) as Record<string, string>;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...customHeaders,
  };
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem('ops_token');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Unknown error' }));
    const detail = (body as { detail?: unknown })?.detail;
    throw new Error(
      typeof detail === 'string' ? detail
        : Array.isArray(detail) ? ((detail[0] as { msg?: string })?.msg ?? JSON.stringify(detail))
        : 'Request failed'
    );
  }
  return res.json() as Promise<T>;
}

export async function apiFetchForm<T>(path: string, formData: FormData, method: 'POST' | 'PATCH' = 'POST'): Promise<T> {
  const token = localStorage.getItem('ops_token');
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (res.status === 401) {
    localStorage.removeItem('ops_token');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Unknown error' }));
    const detail = (body as { detail?: unknown })?.detail;
    throw new Error(
      typeof detail === 'string' ? detail
        : Array.isArray(detail) ? ((detail[0] as { msg?: string })?.msg ?? JSON.stringify(detail))
        : 'Request failed'
    );
  }
  return res.json() as Promise<T>;
}
