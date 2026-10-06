import { AlertTriangle, CircleCheck, ShieldAlert, ShieldCheck } from "lucide-react";
import type { RiskLevel } from "@/types/trustgraph";

const meta: Record<RiskLevel, { label: string; className: string; icon: typeof ShieldCheck }> = {
  SAFE: { label: "SAFE", className: "risk-safe", icon: ShieldCheck },
  LOW: { label: "LOW RISK", className: "risk-low", icon: ShieldCheck },
  CAUTION: { label: "CAUTION", className: "risk-caution", icon: AlertTriangle },
  HIGH: { label: "HIGH RISK", className: "risk-high", icon: ShieldAlert },
  CRITICAL: { label: "CRITICAL", className: "risk-critical", icon: ShieldAlert },
};

export function RiskBadge({ level, small = false }: { level: RiskLevel; small?: boolean }) {
  const item = meta[level] ?? meta.CAUTION;
  const Icon = item.icon;
  return <span className={`risk-badge ${item.className} ${small ? "risk-badge-small" : ""}`} data-testid={`risk-badge-${level.toLowerCase()}`}><Icon size={small ? 12 : 14} strokeWidth={2.5} /><span>{item.label}</span></span>;
}

export function StatusBadge({ reviewed }: { reviewed: boolean }) {
  return <span className={`status-badge ${reviewed ? "status-reviewed" : "status-new"}`} data-testid={`status-badge-${reviewed ? "reviewed" : "new"}`}>{reviewed ? <CircleCheck size={12} /> : <span className="size-1.5 rounded-full bg-current" />}{reviewed ? "Reviewed" : "New"}</span>;
}
