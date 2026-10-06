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
  updateProfile: (name: string) => apiClient.patch<User>("/auth/profile", { name: name.trim() }),
  changePassword: async (currentPassword: string, newPassword: string) =>
    (await apiClient.post<AccountResponse>("/auth/password", { current_password: currentPassword, new_password: newPassword })).user,
  deleteAccount: async (password: string) => { await apiClient.delete("/auth/account", { password, confirmation: "DELETE" }); },
  forgotPassword: (_email: string) => recoveryUnavailable(),
  resetPassword: (_password: string) => recoveryUnavailable(),
};
