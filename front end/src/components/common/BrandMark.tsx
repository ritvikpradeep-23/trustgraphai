import { ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return <Link to="/" className="flex items-center gap-3" aria-label="TrustGraph home" data-testid="brand-mark-link"><span className="grid size-9 place-items-center rounded-xl bg-[#2F66F0] text-white shadow-[0_0_25px_rgba(47,102,240,.4)]"><ShieldCheck size={20} strokeWidth={2.5} /></span>{!compact && <span className="brand-wordmark font-heading text-lg font-bold tracking-tight text-[#F1F5FF]">Trust<span className="text-[#9DBBFF]">Graph</span></span>}</Link>;
}
