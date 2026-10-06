import { appConfig } from "@/config/appConfig";
import { apiClient, ServiceError } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import { filterDetectionList } from "@/lib/detectionData";
import type { Detection, DetectionFilters, Feedback } from "@/types/trustgraph";
const unsupported = () => Promise.reject(new ServiceError("The backend does not implement history deletion or review updates.", 501));
export const detectionService = {
  all: () => apiClient.get<Detection[]>("/workspace/detections"),
  list: async (query: DetectionFilters) => appConfig.USE_MOCK ? mockApi.detections(query) : filterDetectionList(await detectionService.all(), query),
  get: async (id: string): Promise<Detection | null> => {
    if (appConfig.USE_MOCK) return mockApi.detection(id);
    try { return await apiClient.get<Detection>(`/workspace/detections/${encodeURIComponent(id)}`); }
    catch (error) { if (error instanceof ServiceError && error.status === 404) return null; throw error; }
  },
  update: (id: string, patch: { status?: "new" | "reviewed"; feedback?: Feedback }) => appConfig.USE_MOCK ? mockApi.updateDetection(id, patch) : unsupported(),
  clear: () => appConfig.USE_MOCK ? mockApi.clearHistory() : unsupported(),
};
