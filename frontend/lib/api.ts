const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api").replace(/\/$/, "");

export type ApiList<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getToken() {
  return typeof window === "undefined" ? null : window.sessionStorage.getItem("fithub_access");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const url = /^https?:\/\//.test(path) ? path : `${API_BASE}${path}`;
  let response: Response;
  try {
    response = await fetch(url, { ...init, headers, cache: "no-store" });
  } catch {
    throw new ApiError("Could not reach the FitHub API. Check that the backend is running.", 0);
  }
  if (response.status === 401 && !path.includes("/auth/token/")) {
    const refresh = window.sessionStorage.getItem("fithub_refresh");
    if (refresh) {
      try {
        const renewed = await fetch(`${API_BASE}/auth/token/refresh/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
          cache: "no-store",
        });
        if (renewed.ok) {
          const tokens = await renewed.json() as { access: string; refresh?: string };
          saveToken(tokens.access, tokens.refresh || refresh);
          headers.set("Authorization", `Bearer ${tokens.access}`);
          response = await fetch(url, { ...init, headers, cache: "no-store" });
        } else {
          clearToken();
        }
      } catch {
        clearToken();
      }
    }
  }
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : Object.entries(body)
        .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`)
        .join(" ");
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function saveToken(access: string, refresh: string) {
  window.sessionStorage.setItem("fithub_access", access);
  window.sessionStorage.setItem("fithub_refresh", refresh);
}

export function clearToken() {
  window.sessionStorage.removeItem("fithub_access");
  window.sessionStorage.removeItem("fithub_refresh");
}
