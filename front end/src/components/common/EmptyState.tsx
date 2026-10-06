import { Inbox, PlugZap } from "lucide-react";
import { Link } from "react-router-dom";
import { appConfig } from "@/config/appConfig";

export function EmptyState({ title = "No detections yet", description = appConfig.USE_MOCK ? "Use the TrustGraph extension while browsing to start checking messages." : "No stored detections were returned by the backend. Analysis checks are not automatically saved.", action = true }: { title?: string; description?: string; action?: boolean }) {
  return <div className="empty-state" data-testid="empty-state"><span className="empty-icon"><Inbox size={22} /></span><h3 data-testid="empty-state-title">{title}</h3><p data-testid="empty-state-description">{description}</p>{action && <Link to={appConfig.USE_MOCK ? "/app/settings" : "/app/analyze"} className="button-secondary" data-testid="empty-state-settings-link"><PlugZap size={16} />{appConfig.USE_MOCK ? "Extension settings" : "Try the analysis API"}</Link>}</div>;
}
