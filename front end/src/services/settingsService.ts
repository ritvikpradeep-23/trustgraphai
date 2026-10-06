import { appConfig } from "@/config/appConfig";
import { apiClient } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import { getLocalPreferences, updateLocalPreferences } from "@/lib/localPreferences";
import { detectionService } from "./detectionService";
import type { Settings } from "@/types/trustgraph";
export const settingsService = {
  get: async () => appConfig.USE_MOCK ? mockApi.settings() : getLocalPreferences(),
  update: async (patch: Partial<Settings>) => appConfig.USE_MOCK ? mockApi.updateSettings(patch) : updateLocalPreferences(patch),
  // A one-time code the browser extension trades for its sync token (POST /api/extension/pair). Valid 10 minutes.
  regenerateKey: async () => appConfig.USE_MOCK ? mockApi.regenerateKey() : { ...getLocalPreferences(), extensionKey: (await apiClient.post<{ code: string }>("/extension/pairing-code")).code },
  exportData: async () => ({ exportedAt: new Date().toISOString(), detections: appConfig.USE_MOCK ? (await mockApi.detections({ page: 1, pageSize: Number.MAX_SAFE_INTEGER })).items : await detectionService.all(), settings: await settingsService.get() }),
};
