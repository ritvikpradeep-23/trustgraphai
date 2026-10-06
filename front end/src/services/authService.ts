import { appConfig } from "@/config/appConfig";
import { apiClient } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import type { User } from "@/types/trustgraph";

export const authService = {
  login: (email: string, password: string, remember = true) => appConfig.USE_MOCK ? mockApi.login(email, password, remember) : apiClient.post<User>("/auth/login", { email, password, remember }),
  register: (name: string, email: string, password: string) => appConfig.USE_MOCK ? mockApi.register(name, email) : apiClient.post<User>("/auth/register", { name, email, password }),
  logout: () => appConfig.USE_MOCK ? mockApi.logout() : apiClient.post<void>("/auth/logout"),
  deleteAccount: () => appConfig.USE_MOCK ? mockApi.deleteAccount() : apiClient.delete<void>("/auth/account"),
  me: () => appConfig.USE_MOCK ? mockApi.me() : apiClient.get<User | null>("/auth/me"),
  forgotPassword: (email: string) => appConfig.USE_MOCK ? Promise.resolve({ message: `If an account exists for ${email}, a reset link is ready.` }) : apiClient.post<{ message: string }>("/auth/forgot-password", { email }),
  resetPassword: (password: string) => appConfig.USE_MOCK ? Promise.resolve({ message: "Password reset complete." }) : apiClient.post<{ message: string }>("/auth/reset-password", { password }),
};
