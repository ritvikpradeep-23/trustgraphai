import type { RiskLevel } from "@/types/trustgraph";
const colors: Record<RiskLevel, string> = { SAFE: "#3EE6A8", LOW: "#3EE6A8", CAUTION: "#FFB938", HIGH: "#FF5468", CRITICAL: "#E0384D", PENDING: "#7E92C3", UNKNOWN: "#7E92C3" };
export function ScoreRing({ score, level, size = 108, metric = "Risk score" }: { score: number | null; level: RiskLevel; size?: number; metric?: string }) {
  const radius = 44, circumference = 2 * Math.PI * radius, color = colors[level];
  const available = score !== null && Number.isFinite(score) && level !== "PENDING" && level !== "UNKNOWN";
  const value = available ? Math.round(score! * 100) : null;
  return <div className="score-ring" style={{ width: size, height: size }} data-testid="detection-score-ring"><svg viewBox="0 0 100 100" aria-label={available ? `${metric} ${value} percent` : `${metric} unavailable`}><circle cx="50" cy="50" r={radius} fill="none" stroke="#243A6B" strokeWidth="8" />{available && <circle cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - score!)} transform="rotate(-90 50 50)" />}</svg><span className="score-ring-label"><strong>{value ?? "—"}</strong><small>{available ? metric === "Text similarity" ? "similarity" : "/100" : level === "UNKNOWN" ? "no match" : "pending"}</small></span></div>;
}
