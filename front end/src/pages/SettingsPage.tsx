import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Check, Download, Mail, RefreshCw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { ChangePasswordForm } from "@/components/auth/ChangePasswordForm";
import { useAuth } from "@/context/AuthContext";
import { appConfig } from "@/config/appConfig";
import { detectionService } from "@/services/detectionService";
import { settingsService } from "@/services/settingsService";
import type { Settings } from "@/types/trustgraph";

const message = (error: unknown) => error instanceof Error ? error.message : "Could not save this change. Try again.";
function SectionTitle({ eyebrow, title }: { eyebrow: string; title: string }) { return <div className="detail-section-title"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div>; }

export function SettingsPage() {
  const { user, refreshUser, deleteAccount } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const query = useQuery({ queryKey: ["settings"], queryFn: settingsService.get });
  const [name, setName] = useState("");
  const [minutes, setMinutes] = useState("");
  const [nameError, setNameError] = useState("");
  const [minutesError, setMinutesError] = useState("");
  const [saved, setSaved] = useState(false);
  const [confirm, setConfirm] = useState<"history" | "account" | null>(null);
  const [deletePassword, setDeletePassword] = useState("");
  useEffect(() => { if (query.data?.name !== undefined) setName(query.data.name); }, [query.data?.name]);
  useEffect(() => { if (query.data?.minutesSavedPerCheck !== undefined) setMinutes(String(query.data.minutesSavedPerCheck)); }, [query.data?.minutesSavedPerCheck]);
  useEffect(() => { if (!saved) return; const timer = window.setTimeout(() => setSaved(false), 2000); return () => window.clearTimeout(timer); }, [saved]);
  const update = useMutation({
    mutationFn: (patch: Partial<Settings>) => settingsService.update(patch),
    onMutate: patch => {
      void queryClient.cancelQueries({ queryKey: ["settings"] });
      const previous = queryClient.getQueryData<Settings>(["settings"]);
      if (previous) queryClient.setQueryData(["settings"], { ...previous, ...patch, notifications: { ...previous.notifications, ...patch.notifications } });
      return { previous };
    },
    onSuccess: async next => { queryClient.setQueryData(["settings"], next); await refreshUser().catch(() => toast.error("Changes saved, but the profile could not refresh. Reload the page.")); setNameError(""); setMinutesError(""); setSaved(true); toast.success("Changes saved."); },
    onError: (failure, _, context) => { if (context?.previous) queryClient.setQueryData(["settings"], context.previous); toast.error(message(failure)); },
  });
  const keyMutation = useMutation({ mutationFn: settingsService.regenerateKey, onSuccess: next => { queryClient.setQueryData(["settings"], next); toast.success(appConfig.USE_MOCK ? "Demo extension key regenerated." : "Pairing code ready. Enter it in the extension within 10 minutes."); }, onError: failure => toast.error(message(failure)) });
  const deletion = useMutation({
    mutationFn: async (kind: "history" | "account") => { if (kind === "history") await detectionService.clear(); else await deleteAccount(deletePassword); },
    onSuccess: async (_, kind) => { setConfirm(null); setDeletePassword(""); if (kind === "history") { await queryClient.invalidateQueries(); toast.success("Detection history deleted."); } else navigate("/", { replace: true }); },
    onError: failure => toast.error(message(failure)),
  });
  const exportData = async () => {
    try {
      const data = await settingsService.exportData();
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const link = document.createElement("a"); link.href = url; link.download = "trustgraph-export.json"; document.body.append(link); link.click(); link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast.success("Your data export is ready.");
    } catch (failure) { toast.error(message(failure)); }
  };
  if (query.isLoading) return <div className="loading-state"><span className="loading-spinner" />Loading settings…</div>;
  if (query.isError || !query.data) return <div className="inline-error">Could not load settings.<button className="button-secondary" onClick={() => void query.refetch()}>Try again</button></div>;
  const settings = query.data;
  return <div className="page-stack">
    <div className="page-header"><div><span className="eyebrow">Workspace controls</span><h1>Settings that stay yours.</h1><p>{appConfig.USE_MOCK ? "These preferences are saved in this browser only." : "Display preferences stay in this browser. Your account and extension verdicts are stored on the backend. Pair your extension below."}</p></div>{saved && <span className="save-confirm" role="status" data-testid="settings-saved-message"><Check size={15} />Saved</span>}</div>
    <div className="settings-layout">
      <nav className="settings-nav" aria-label="Settings sections"><a href="#account" data-testid="settings-nav-account">Account</a><a href="#notifications" data-testid="settings-nav-notifications">Notifications</a><a href="#detection" data-testid="settings-nav-detection">Detection preferences</a><a href="#privacy" data-testid="settings-nav-privacy">Privacy</a></nav>
      <div className="settings-sections">
        <section className="panel settings-section" id="account"><SectionTitle eyebrow="Identity" title="Account" />
          <form noValidate onSubmit={event => { event.preventDefault(); setNameError(""); if (!name.trim()) { setNameError("Profile name cannot be empty."); return; } update.mutate({ name: name.trim() }); }}>
            <div className="settings-fields"><label>Profile name<input value={name} maxLength={100} onChange={event => setName(event.target.value)} autoComplete="name" data-testid="settings-name-input" /></label><label>Email address<div className="input-with-icon"><Mail size={15} /><input value={user?.email ?? settings.email} readOnly data-testid="settings-email-input" /></div></label></div>
            {nameError && <div className="form-error" role="alert" data-testid="settings-name-error">{nameError}</div>}
            <button type="submit" className="button-secondary settings-save-button" disabled={update.isPending} data-testid="settings-save-profile">{update.isPending ? "Saving…" : "Save profile"}</button>
          </form>
          {!appConfig.USE_MOCK && <ChangePasswordForm />}
          <div className="session-row"><div><strong>{appConfig.USE_MOCK ? "Active sessions" : "Local preferences"}</strong><p>This browser only</p></div><span className="security-ok">{appConfig.USE_MOCK ? "Active now" : "Cookie session"}</span></div>
        </section>
        <section className="panel settings-section" id="notifications"><SectionTitle eyebrow="Stay informed" title="Notifications" />{!appConfig.USE_MOCK && <p className="empty-period-note">Notifications are unavailable until a notification service is connected.</p>}
          <div className="toggle-list">{([["security", "Security alerts", "Important changes and unusual activity"], ["detection", "Detection updates", "A summary when new results arrive"], ["account", "Account updates", "Product and workspace notices"]] as const).map(([key, title, body]) => <label className="toggle-row" key={key}><span><strong>{title}</strong><small>{body}</small></span><input type="checkbox" aria-label={title} checked={settings.notifications[key]} disabled={!appConfig.USE_MOCK || update.isPending} onChange={event => update.mutate({ notifications: { ...settings.notifications, [key]: event.target.checked } })} data-testid={`settings-notification-${key}-toggle`} /><i aria-hidden="true" /></label>)}</div>
        </section>
        <section className="panel settings-section" id="detection"><SectionTitle eyebrow="Time saved estimate" title="Detection preferences" />
          <form noValidate onSubmit={event => { event.preventDefault(); setMinutesError(""); const value = Number(minutes); if (!minutes.trim() || !Number.isInteger(value) || value < 1 || value > 60) { setMinutesError("Enter a whole number from 1 to 60."); return; } update.mutate({ minutesSavedPerCheck: value }); }}>
            <label className="minutes-field">Minutes saved per check<span>Used only for the dashboard estimate.</span><div><input type="number" min="1" max="60" step="1" inputMode="numeric" value={minutes} onChange={event => setMinutes(event.target.value)} data-testid="settings-minutes-input" /><span>minutes</span></div></label>
            {minutesError && <div className="form-error" role="alert" data-testid="settings-minutes-error">{minutesError}</div>}
            <button type="submit" className="button-secondary settings-save-button" disabled={update.isPending} data-testid="settings-save-minutes">Save estimate</button>
          </form>
          <div className="extension-key-row"><div><span className="eyebrow">{appConfig.USE_MOCK ? "Browser extension key" : "Browser extension pairing code"}</span><strong className="mono-text" data-testid="settings-extension-key">{settings.extensionKey}</strong><p>{appConfig.USE_MOCK ? "Illustrative key for this demo workspace." : "In the extension popup, enter this code under “Have a pairing code?”. It works once, for 10 minutes. Paired, the extension adds its verdicts (never message text) to this workspace."}</p></div><button className="button-secondary" type="button" onClick={() => keyMutation.mutate()} disabled={keyMutation.isPending || update.isPending} data-testid="settings-regenerate-key-button"><RefreshCw size={15} />{keyMutation.isPending ? (appConfig.USE_MOCK ? "Regenerating…" : "Creating…") : appConfig.USE_MOCK ? "Regenerate" : "New code"}</button></div>
        </section>
        <section className="panel settings-section" id="privacy"><SectionTitle eyebrow="Your data" title="Privacy controls" />
          <div className="privacy-actions"><button type="button" disabled={deletion.isPending} onClick={() => setConfirm("history")} data-testid="settings-delete-history-button"><Trash2 size={17} /><span><strong>Delete my history</strong><small>Remove your website and synced extension results.</small></span><ArrowRight size={15} /></button><button type="button" onClick={() => void exportData()} data-testid="settings-export-button"><Download size={17} /><span><strong>Export my data</strong><small>Download detections and settings as a JSON file.</small></span><ArrowRight size={15} /></button><button type="button" className="danger-action" disabled={deletion.isPending} onClick={() => { setDeletePassword(""); setConfirm("account"); }} data-testid="settings-delete-account-button"><Trash2 size={17} /><span><strong>Delete my account</strong><small>Remove your account and verdicts, revoke paired extensions and sign out.</small></span><ArrowRight size={15} /></button></div>
        </section>
      </div>
    </div>
    {confirm && <ConfirmDialog title={confirm === "history" ? "Delete your history?" : "Permanently delete this account?"} description={confirm === "history" ? "This permanently removes your website and synced extension results, not other accounts. It does not clear the extension’s local storage; future synced checks can appear." : "This permanently deletes your account and verdicts, revokes sessions and extension tokens, and signs you out. Enter your current password to confirm."} confirmLabel={confirm === "history" ? "Delete history" : "Delete account permanently"} busy={deletion.isPending} confirmDisabled={confirm === "account" && !deletePassword} onClose={() => { setConfirm(null); setDeletePassword(""); }} onConfirm={() => deletion.mutate(confirm)}>
      {confirm === "account" && <label className="minutes-field">Current password<input type="password" autoComplete="current-password" maxLength={128} value={deletePassword} disabled={deletion.isPending} onChange={event => setDeletePassword(event.target.value)} data-testid="settings-delete-password-input" /></label>}
    </ConfirmDialog>}
  </div>;
}
