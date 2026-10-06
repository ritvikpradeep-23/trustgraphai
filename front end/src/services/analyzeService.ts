import { apiClient, ServiceError } from "./apiClient";
import { appConfig } from "@/config/appConfig";
import type { RiskLevel } from "@/types/trustgraph";

export interface AnalysisResult {
  method: string;
  previous_report_matches: { report_id: string; report_type: string; status: string; similarity_score: number }[];
  detection_id: string;
  risk_score: number | null;
  risk_level: RiskLevel;
  signals: Record<string, number | null>;
  reasons: string[];
  ai_written: { available: boolean; reasons: string[] } | null;
}
export interface UrlResult {
  normalized_url: string;
  hostname: string;
  registrable_domain: string;
  signals: Record<string, boolean>;
  reasons: string[];
}
function liveOnly() {
  if (appConfig.USE_MOCK) throw new ServiceError("Analysis requires live mode. Set VITE_USE_MOCK=false and start the backend.", 501);
}
export const analyzeService = {
  text: (text: string, channel: string) => {
    liveOnly();
    return apiClient.post<AnalysisResult>("/detect", { text, channel });
  },
  url: (url: string) => {
    liveOnly();
    return apiClient.post<UrlResult>("/url/analyze", { url });
  },
};
