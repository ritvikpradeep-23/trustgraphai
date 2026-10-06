import { appConfig } from "@/config/appConfig";
import { mockApi } from "@/mock/mockApi";
import { detectionService } from "./detectionService";
import { buildAnalytics } from "@/lib/detectionData";
import type { DateRange } from "@/types/trustgraph";
export const analyticsService = { get: async (range?: DateRange) => appConfig.USE_MOCK ? mockApi.analytics(range) : buildAnalytics(await detectionService.all(), range) };
