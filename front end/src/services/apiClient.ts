import { appConfig } from "@/config/appConfig";
let csrfToken: string | null = null;
export class ServiceError extends Error {
  status: number;
  constructor(message: string, status = 400) { super(message); this.status = status; this.name = "ServiceError"; }
}
const request = async <T>(method: string, path: string, body?: unknown): Promise<T> => {
  if (method !== "GET" && !csrfToken) await request("GET", "/auth/session");
  let response: Response;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    response = await fetch(`${appConfig.API_BASE_URL.replace(/\/$/, "")}${path}`, {
      method, signal: controller.signal, credentials: "include",
      headers: { ...(body === undefined ? {} : { "Content-Type": "application/json" }), ...(method !== "GET" && csrfToken ? { "X-CSRF-Token": csrfToken } : {}) },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch { throw new ServiceError("Cannot reach the backend. Start python run_server.py and check the API URL.", 0); }
  finally { clearTimeout(timeout); }
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = typeof data?.detail === "string" ? data.detail : Array.isArray(data?.detail) ? data.detail.map((item: { msg?: string }) => item.msg).join("; ") : `Backend request failed (${response.status}).`;
    throw new ServiceError(detail, response.status);
  }
  if (response.status === 204) return undefined as T;
  if (!response.headers.get("content-type")?.includes("application/json")) throw new ServiceError("Expected JSON from the backend. Check the /api proxy configuration.", 502);
  const data: unknown = await response.json();
  if (data && typeof data === "object" && "csrfToken" in data && typeof data.csrfToken === "string") csrfToken = data.csrfToken;
  if (path === "/auth/logout") csrfToken = null;
  return data as T;
};
export const apiClient = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
};
