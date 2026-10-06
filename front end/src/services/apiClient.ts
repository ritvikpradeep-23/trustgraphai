import { appConfig } from "@/config/appConfig";

export class ServiceError extends Error {
  status: number;
  constructor(message: string, status = 400) { super(message); this.name = "ServiceError"; this.status = status; }
}

const request = async <T>(method: string, path: string, body?: unknown): Promise<T> => {
  const response = await fetch(`${appConfig.API_BASE_URL}${path}`, { method, headers: body === undefined ? undefined : { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body), credentials: "include" });
  if (!response.ok) throw new ServiceError("Request failed", response.status);
  return response.status === 204 ? (undefined as T) : (await response.json() as T);
};

export const apiClient = {
  get: <T>(path: string) => appConfig.USE_MOCK ? Promise.reject(new ServiceError("Mock handler missing")) : request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => appConfig.USE_MOCK ? Promise.reject(new ServiceError("Mock handler missing")) : request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => appConfig.USE_MOCK ? Promise.reject(new ServiceError("Mock handler missing")) : request<T>("PUT", path, body),
  patch: <T>(path: string, body?: unknown) => appConfig.USE_MOCK ? Promise.reject(new ServiceError("Mock handler missing")) : request<T>("PATCH", path, body),
  delete: <T>(path: string) => appConfig.USE_MOCK ? Promise.reject(new ServiceError("Mock handler missing")) : request<T>("DELETE", path),
};
