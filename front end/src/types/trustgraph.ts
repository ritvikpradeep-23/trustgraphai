export type RiskLevel = "SAFE" | "LOW" | "CAUTION" | "HIGH" | "CRITICAL" | "PENDING" | "UNKNOWN";
export type Channel = "whatsapp" | "gmail" | "messenger" | "instagram" | "other";
export type DetectionStatus = "new" | "reviewed";
export type Feedback = "none" | "right" | "false_alarm";

export interface DateRange { from?: string; to?: string }
export interface DetectionFilters extends DateRange { q?: string; level?: string; page?: number; pageSize?: number }

export interface Signal {
  name: string;
  score: number | null;
  explanation: string;
}

export interface Detection {
  id: string;
  createdAt: string;
  channel: Channel;
  site: string;
  riskLevel: RiskLevel;
  riskScore: number | null;
  explanation: string;
  signals: Signal[];
  confidence?: number;
  engineVersion: string;
  extracted?: Record<string, string>;
  urlIntelligence?: { domain: string; reputation: string; age: string };
  patternAnalysis?: { match: string; detail: string };
  recommendation?: string;
  status: DetectionStatus;
  feedback: Feedback;
  isDemo: boolean;
  editable?: boolean;
}

export interface User {
  id: string;
  name: string;
  email: string;
  joinedAt: string;
}

export interface ExtensionStatus {
  state: "CONNECTED" | "NOT CONNECTED" | "UNKNOWN";
  lastSeen: string | null;
}

export interface Settings {
  name: string;
  email: string;
  minutesSavedPerCheck: number;
  notifications: { security: boolean; detection: boolean; account: boolean };
  extensionKey: string;
}

export interface DetectionList {
  items: Detection[];
  total: number;
  page: number;
  pageSize: number;
}

export interface AnalyticsSummary {
  total: number;
  low: number;
  caution: number;
  high: number;
  reviewed: number;
  highRate: number | null;
  pending: number;
}

export interface AnalyticsPoint {
  label: string;
  total: number;
  high: number;
  caution: number;
}

export interface ChannelPoint {
  channel: Channel;
  count: number;
}

export interface AnalyticsData {
  summary: AnalyticsSummary;
  timeseries: AnalyticsPoint[];
  distribution: { label: string; count: number; color: string }[];
  channels: ChannelPoint[];
}
