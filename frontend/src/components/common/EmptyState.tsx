import { Inbox, PlugZap } from "lucide-react";
import { Link } from "react-router-dom";

export function EmptyState({ title = "No detections yet", description = "Use the TrustGraph extension while browsing to start checking messages.", action = true }: { title?: string; description?: string; action?: boolean }) {
  return <div className="empty-state" data-testid="empty-state"><span className="empty-icon"><Inbox size={22} /></span><h3 data-testid="empty-state-title">{title}</h3><p data-testid="empty-state-description">{description}</p>{action && <Link to="/app/settings" className="button-secondary" data-testid="empty-state-settings-link"><PlugZap size={16} />Extension settings</Link>}</div>;
}
