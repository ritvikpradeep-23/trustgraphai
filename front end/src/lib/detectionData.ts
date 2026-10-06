import type { AnalyticsData, DateRange, Detection, DetectionFilters, DetectionList } from "../types/trustgraph.ts";

export function dateRangeForDays(days: number, now = new Date()): DateRange {
  const from = new Date(now);
  from.setDate(from.getDate() - days + 1);
  from.setHours(0, 0, 0, 0);
  return { from: from.toISOString(), to: now.toISOString() };
}

export function detectionsInRange(items: Detection[], range: DateRange = {}) {
  const from = range.from ? new Date(range.from).getTime() : -Infinity;
  const to = range.to ? new Date(range.to).getTime() : Infinity;
  return items.filter(item => {
    const time = new Date(item.createdAt).getTime();
    return Number.isFinite(time) && time >= from && time <= to;
  });
}

export function filterDetectionList(items: Detection[], query: DetectionFilters = {}): DetectionList {
  const search = query.q?.trim().toLowerCase() ?? "";
  const filtered = detectionsInRange(items, query)
    .filter(item => (!search || `${item.id} ${item.site} ${item.channel}`.toLowerCase().includes(search)) && (!query.level || (query.level === "HIGH_RISK" ? item.riskLevel === "HIGH" || item.riskLevel === "CRITICAL" : item.riskLevel === query.level)))
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime() || a.id.localeCompare(b.id));
  const pageSize = Number.isFinite(query.pageSize) ? Math.max(1, Math.floor(query.pageSize!)) : 8;
  const requestedPage = Number.isFinite(query.page) ? Math.max(1, Math.floor(query.page!)) : 1;
  const page = Math.min(requestedPage, Math.max(1, Math.ceil(filtered.length / pageSize)));
  return { items: filtered.slice((page - 1) * pageSize, page * pageSize), total: filtered.length, page, pageSize };
}

export function buildAnalytics(items: Detection[], range: DateRange = {}, now = new Date()): AnalyticsData {
  const detections = detectionsInRange(items, { ...range, to: range.to ?? now.toISOString() });
  const low = detections.filter(item => item.riskLevel === "LOW" || item.riskLevel === "SAFE").length;
  const caution = detections.filter(item => item.riskLevel === "CAUTION").length;
  const high = detections.filter(item => item.riskLevel === "HIGH" || item.riskLevel === "CRITICAL").length;
  const pending = detections.filter(item => item.riskLevel === "PENDING").length;
  const assessed = low + caution + high;
  const end = new Date(range.to ?? now);
  const earliest = detections.length ? Math.min(...detections.map(item => new Date(item.createdAt).getTime())) : dateRangeForDays(7, end).from!;
  const start = new Date(range.from ?? earliest);
  start.setHours(0, 0, 0, 0);
  const days: Date[] = [];
  for (const day = new Date(start); day <= end; day.setDate(day.getDate() + 1)) days.push(new Date(day));
  const count = Math.min(7, days.length);
  const timeseries = Array.from({ length: count }, (_, index) => {
    const day = days[Math.round(index * (days.length - 1) / Math.max(count - 1, 1))];
    const cutoff = new Date(day);
    cutoff.setHours(23, 59, 59, 999);
    const slice = detections.filter(item => new Date(item.createdAt) <= cutoff);
    return {
      label: day.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      total: slice.length,
      high: slice.filter(item => item.riskLevel === "HIGH" || item.riskLevel === "CRITICAL").length,
      caution: slice.filter(item => item.riskLevel === "CAUTION").length,
    };
  });
  return {
    summary: { total: detections.length, low, caution, high, pending, reviewed: detections.filter(item => item.status === "reviewed").length, highRate: assessed ? Math.round(high / assessed * 100) : null },
    timeseries,
    distribution: [{ label: "Low / safe", count: low, color: "#3EE6A8" }, { label: "Caution", count: caution, color: "#FFB938" }, { label: "High / critical", count: high, color: "#FF5468" }, ...(pending ? [{ label: "Pending", count: pending, color: "#7E92C3" }] : [])],
    channels: (["whatsapp", "gmail", "messenger", "instagram", "other"] as const).map(channel => ({ channel, count: detections.filter(item => item.channel === channel).length })),
  };
}
