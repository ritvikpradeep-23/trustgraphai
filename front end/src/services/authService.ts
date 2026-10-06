import { apiClient, ServiceError } from "@/services/apiClient";
import type { User } from "@/types/trustgraph";

interface SessionResponse { user: User | null; csrfToken: string }
interface AccountResponse extends SessionResponse { user: User }
const recoveryUnavailable = () => Promise.reject(new ServiceError("Password recovery requires a verified email delivery service. Contact your administrator; no reset email was sent.", 501));

export const authService = {
  login: async (email: string, password: string, remember = false) =>
    (await apiClient.post<AccountResponse>("/auth/login", { email: email.trim(), password, remember })).user,
  register: async (name: string, email: string, password: string) =>
    (await apiClient.post<AccountResponse>("/auth/register", { name: name.trim(), email: email.trim(), password, remember: false })).user,
  me: async () => (await apiClient.get<SessionResponse>("/auth/session")).user,
  logout: async () => { await apiClient.post("/auth/logout"); },
  deleteAccount: () => Promise.reject(new ServiceError("Account deletion is not configured. Contact your administrator.", 501)),
  forgotPassword: (_email: string) => recoveryUnavailable(),
  resetPassword: (_password: string) => recoveryUnavailable(),
};
