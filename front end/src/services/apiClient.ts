import { appConfig } from "@/config/appConfig";
export class ServiceError extends Error {
  status: number;
  constructor(message: string, status = 400) { super(message); this.status = status; this.name = "ServiceError"; }
}
const request = async <T>(method: string, path: string, body?: unknown): Promise<T> => {
  let response: Response;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    response = await fetch(`${appConfig.API_BASE_URL.replace(/\/$/, "")}${path}`, {
      method, signal: controller.signal,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
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
  return response.json() as Promise<T>;
};
export const apiClient = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
};
