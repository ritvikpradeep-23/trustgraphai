import { appConfig } from "@/config/appConfig";
import { apiClient, ServiceError } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import { filterDetectionList } from "@/lib/detectionData";
import type { Detection, DetectionFilters, Feedback } from "@/types/trustgraph";
export const detectionService = {
  all: () => apiClient.get<Detection[]>("/workspace/detections"),
  list: async (query: DetectionFilters) => appConfig.USE_MOCK ? mockApi.detections(query) : filterDetectionList(await detectionService.all(), query),
  get: async (id: string): Promise<Detection | null> => {
    if (appConfig.USE_MOCK) return mockApi.detection(id);
    try { return await apiClient.get<Detection>(`/workspace/detections/${encodeURIComponent(id)}`); }
    catch (error) { if (error instanceof ServiceError && error.status === 404) return null; throw error; }
  },
  update: (id: string, patch: { status?: "new" | "reviewed"; feedback?: Feedback }) => appConfig.USE_MOCK ? mockApi.updateDetection(id, patch) : apiClient.patch<Detection>(`/workspace/detections/${encodeURIComponent(id)}`, patch),
  clear: () => appConfig.USE_MOCK ? mockApi.clearHistory() : apiClient.delete("/workspace/detections"),
};
