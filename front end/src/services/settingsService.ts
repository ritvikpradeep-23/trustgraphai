import { appConfig } from "@/config/appConfig";
import { mockApi } from "@/mock/mockApi";
import { getLocalPreferences, updateLocalPreferences } from "@/lib/localPreferences";
import { detectionService } from "./detectionService";
import type { Settings } from "@/types/trustgraph";
export const settingsService = {
  get: async () => appConfig.USE_MOCK ? mockApi.settings() : getLocalPreferences(),
  update: async (patch: Partial<Settings>) => appConfig.USE_MOCK ? mockApi.updateSettings(patch) : updateLocalPreferences(patch),
  regenerateKey: () => appConfig.USE_MOCK ? mockApi.regenerateKey() : Promise.reject(new Error("The backend has no extension pairing API.")),
  exportData: async () => ({ exportedAt: new Date().toISOString(), detections: appConfig.USE_MOCK ? (await mockApi.detections({ page: 1, pageSize: Number.MAX_SAFE_INTEGER })).items : await detectionService.all(), settings: await settingsService.get() }),
};
