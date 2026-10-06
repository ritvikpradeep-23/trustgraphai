import { Beaker, X } from "lucide-react";

export function DemoBanner({ onClear }: { onClear: () => void }) {
  return <div className="demo-banner" data-testid="demo-data-banner"><div className="flex items-center gap-2"><Beaker size={15} /><span><strong>You are viewing demo data</strong><span className="hidden sm:inline"> — these detections are illustrative and never represent real activity.</span></span></div><button type="button" onClick={onClear} data-testid="clear-demo-data-button"><X size={14} />Clear demo data</button></div>;
}
