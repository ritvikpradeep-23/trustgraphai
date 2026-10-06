import { appConfig } from "@/config/appConfig";
import { apiClient } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import { getLocalPreferences, updateLocalPreferences } from "@/lib/localPreferences";
import { detectionService } from "./detectionService";
import { authService } from "./authService";
import type { Settings } from "@/types/trustgraph";
export const settingsService = {
  get: async () => {
    if (appConfig.USE_MOCK) return mockApi.settings();
    const user = await authService.me();
    return { ...getLocalPreferences(), name: user?.name ?? "", email: user?.email ?? "", extensionKey: "Click New code to pair your extension" };
  },
  update: async (patch: Partial<Settings>) => {
    if (appConfig.USE_MOCK) return mockApi.updateSettings(patch);
    if (patch.name !== undefined) await authService.updateProfile(patch.name);
    updateLocalPreferences(patch);
    return settingsService.get();
  },
  // A one-time code the browser extension trades for its sync token (POST /api/extension/pair). Valid 10 minutes.
  regenerateKey: async () => appConfig.USE_MOCK ? mockApi.regenerateKey() : { ...await settingsService.get(), extensionKey: (await apiClient.post<{ code: string }>("/extension/pairing-code")).code },
  exportData: async () => ({ exportedAt: new Date().toISOString(), detections: appConfig.USE_MOCK ? (await mockApi.detections({ page: 1, pageSize: Number.MAX_SAFE_INTEGER })).items : await detectionService.all(), settings: await settingsService.get() }),
};
