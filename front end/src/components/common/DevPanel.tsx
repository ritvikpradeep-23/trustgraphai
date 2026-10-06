import { useState } from "react";
import { Bug, ChevronDown, RotateCcw, Wifi, WifiOff } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { mockApi } from "@/mock/mockApi";
import { extensionService } from "@/services/extensionService";
import type { ExtensionStatus } from "@/types/trustgraph";

const states: ExtensionStatus["state"][] = ["CONNECTED", "NOT CONNECTED", "UNKNOWN"];
export function DevPanel() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["extension-status"], queryFn: extensionService.getStatus });
  const mutation = useMutation({
    mutationFn: (state: ExtensionStatus["state"]) => extensionService.setMockStatus({ state, lastSeen: state === "CONNECTED" ? new Date().toISOString() : null }),
    onSuccess: next => { queryClient.setQueryData(["extension-status"], next); },
    onError: error => toast.error(error instanceof Error ? error.message : "Could not update the preview."),
  });
  return <aside className={`dev-panel ${open ? "dev-panel-open" : ""}`} data-testid="mock-dev-panel">
    <button type="button" className="dev-panel-toggle" aria-expanded={open} aria-controls="mock-preview-controls" onClick={() => setOpen(!open)} data-testid="mock-dev-panel-toggle"><Bug size={14} />Mock preview<ChevronDown size={14} className={open ? "rotate-180" : ""} /></button>
    {open && <div id="mock-preview-controls" className="dev-panel-body"><p>Preview extension states</p>{states.map(item => <button key={item} type="button" disabled={mutation.isPending} aria-pressed={query.data?.state === item} className={`dev-state ${query.data?.state === item ? "dev-state-active" : ""}`} onClick={() => mutation.mutate(item)} data-testid={`mock-status-${item.toLowerCase().replaceAll(" ", "-")}`}>{item === "CONNECTED" ? <Wifi size={14} /> : <WifiOff size={14} />}{item}</button>)}<button type="button" className="dev-reset" onClick={() => { try { mockApi.reset(); void queryClient.invalidateQueries(); toast.success("Demo seed restored."); } catch { toast.error("Could not restore the demo seed."); } }} data-testid="mock-reset-button"><RotateCcw size={13} />Reset demo seed</button></div>}
  </aside>;
}
