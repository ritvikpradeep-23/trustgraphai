import { appConfig } from "@/config/appConfig";
import { mockApi } from "@/mock/mockApi";
import { localWorkspaceIdentity } from "@/lib/localPreferences";
const unavailable = () => Promise.reject(new Error("This local backend has no authentication API. Open the workspace without signing in."));
export const authService = {
  login: (email: string, password: string, remember = true) => appConfig.USE_MOCK ? mockApi.login(email, password, remember) : unavailable(),
  register: (name: string, email: string, _password: string) => appConfig.USE_MOCK ? mockApi.register(name, email) : unavailable(),
  logout: () => appConfig.USE_MOCK ? mockApi.logout() : unavailable(),
  deleteAccount: () => appConfig.USE_MOCK ? mockApi.deleteAccount() : unavailable(),
  me: () => appConfig.USE_MOCK ? mockApi.me() : Promise.resolve(localWorkspaceIdentity()),
  forgotPassword: (_email: string) => appConfig.USE_MOCK ? Promise.resolve({ message: "Demo reset is ready. No email was sent." }) : unavailable(),
  resetPassword: (_password: string) => appConfig.USE_MOCK ? Promise.resolve({ message: "Demo reset complete." }) : unavailable(),
};
