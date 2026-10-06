import type { RiskLevel } from "@/types/trustgraph";

const colors: Record<RiskLevel, string> = { SAFE: "#3EE6A8", LOW: "#3EE6A8", CAUTION: "#FFB938", HIGH: "#FF5468", CRITICAL: "#E0384D" };
export function ScoreRing({ score, level, size = 108 }: { score: number; level: RiskLevel; size?: number }) {
  const radius = 44; const circumference = 2 * Math.PI * radius; const color = colors[level] ?? colors.CAUTION;
  return <div className="score-ring" style={{ width: size, height: size }} data-testid="detection-score-ring"><svg viewBox="0 0 100 100" aria-label={`Risk score ${Math.round(score * 100)} percent`}><circle cx="50" cy="50" r={radius} fill="none" stroke="#243A6B" strokeWidth="8" /><circle cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - score)} transform="rotate(-90 50 50)" /></svg><span className="score-ring-label"><strong>{Math.round(score * 100)}</strong><small>/100</small></span></div>;
}
