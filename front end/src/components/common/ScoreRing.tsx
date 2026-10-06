import type { RiskLevel } from "@/types/trustgraph";
const colors: Record<RiskLevel, string> = { SAFE: "#3EE6A8", LOW: "#3EE6A8", CAUTION: "#FFB938", HIGH: "#FF5468", CRITICAL: "#E0384D", PENDING: "#7E92C3" };
export function ScoreRing({ score, level, size = 108 }: { score: number | null; level: RiskLevel; size?: number }) {
  const radius = 44, circumference = 2 * Math.PI * radius, color = colors[level];
  const available = score !== null && Number.isFinite(score) && level !== "PENDING";
  const value = available ? Math.round(score! * 100) : null;
  return <div className="score-ring" style={{ width: size, height: size }} data-testid="detection-score-ring"><svg viewBox="0 0 100 100" aria-label={available ? `Risk score ${value} percent` : "Risk score unavailable"}><circle cx="50" cy="50" r={radius} fill="none" stroke="#243A6B" strokeWidth="8" />{available && <circle cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - score!)} transform="rotate(-90 50 50)" />}</svg><span className="score-ring-label"><strong>{value ?? "—"}</strong><small>{available ? "/100" : "pending"}</small></span></div>;
}
