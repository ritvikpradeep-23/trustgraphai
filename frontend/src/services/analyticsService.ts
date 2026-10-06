import { appConfig } from "@/config/appConfig";
import { apiClient } from "@/services/apiClient";
import { mockApi } from "@/mock/mockApi";
import type { AnalyticsData, DateRange } from "@/types/trustgraph";

export const analyticsService = { get: (range?: DateRange) => appConfig.USE_MOCK ? mockApi.analytics(range) : apiClient.get<AnalyticsData>(`/analytics/summary?${new URLSearchParams({ from: range?.from ?? "", to: range?.to ?? "" }).toString()}`) };
