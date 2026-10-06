import { appConfig } from "@/config/appConfig";
import { apiClient } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import type { ExtensionStatus } from "@/types/trustgraph";

export const extensionService = { getStatus: () => appConfig.USE_MOCK ? mockApi.status() : apiClient.get<ExtensionStatus>("/extension/status"), setMockStatus: (status: ExtensionStatus) => mockApi.setStatus(status) };
