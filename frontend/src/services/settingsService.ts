import { appConfig } from "@/config/appConfig";
import { apiClient } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import type { Settings } from "@/types/trustgraph";

export const settingsService = {
  get: () => appConfig.USE_MOCK ? mockApi.settings() : apiClient.get<Settings>("/settings"),
  update: (patch: Partial<Settings>) => appConfig.USE_MOCK ? mockApi.updateSettings(patch) : apiClient.put<Settings>("/settings", patch),
  regenerateKey: () => appConfig.USE_MOCK ? mockApi.regenerateKey() : apiClient.post<Settings>("/settings/extension-key"),
  exportData: async () => { const payload = appConfig.USE_MOCK ? { exportedAt: new Date().toISOString(), detections: (await mockApi.detections({ page: 1, pageSize: Number.MAX_SAFE_INTEGER })).items, settings: await mockApi.settings() } : await apiClient.get<unknown>("/export"); return payload; },
};
