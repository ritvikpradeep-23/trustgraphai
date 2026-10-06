import { appConfig } from "@/config/appConfig";
import { apiClient } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import type { Detection, DetectionList, DetectionFilters, Feedback } from "@/types/trustgraph";

export const detectionService = {
  list: (query: DetectionFilters) => appConfig.USE_MOCK ? mockApi.detections(query) : apiClient.get<DetectionList>(`/detections?${new URLSearchParams(Object.entries(query).filter(([, value]) => value !== undefined).map(([key, value]) => [key, String(value)])).toString()}`),
  get: (id: string) => appConfig.USE_MOCK ? mockApi.detection(id) : apiClient.get<Detection>(`/detections/${id}`),
  update: (id: string, patch: { status?: "new" | "reviewed"; feedback?: Feedback }) => appConfig.USE_MOCK ? mockApi.updateDetection(id, patch) : apiClient.patch<Detection>(`/detections/${id}`, patch),
  clear: () => appConfig.USE_MOCK ? mockApi.clearHistory() : apiClient.delete<void>("/detections"),
};
