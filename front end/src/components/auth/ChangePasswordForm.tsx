import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { authService } from "@/services/authService";
import { validatePasswordChange } from "@/lib/passwordValidation";

export function ChangePasswordForm() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const change = useMutation({
    mutationFn: () => authService.changePassword(current, next),
    onSuccess: () => { setCurrent(""); setNext(""); setConfirmation(""); setError(null); toast.success("Password changed. Other website sessions are signed out."); },
    onError: failure => setError(failure instanceof Error ? failure.message : "Could not change your password."),
  });
  return <form noValidate onSubmit={event => {
    event.preventDefault();
    const failure = validatePasswordChange(current, next, confirmation);
    setError(failure);
    if (!failure) change.mutate();
  }}>
    <h3>Change password</h3>
    <p className="empty-period-note">Enter your current password and a new 15–128 character passphrase. Other website sessions will be signed out; paired extensions remain paired.</p>
    <div className="settings-fields">
      <label>Current password<input type="password" autoComplete="current-password" maxLength={128} value={current} disabled={change.isPending} onChange={event => setCurrent(event.target.value)} data-testid="settings-current-password-input" /></label>
      <label>New passphrase<input type="password" autoComplete="new-password" minLength={15} maxLength={128} value={next} disabled={change.isPending} onChange={event => setNext(event.target.value)} data-testid="settings-password-input" /></label>
      <label>Confirm new passphrase<input type="password" autoComplete="new-password" maxLength={128} value={confirmation} disabled={change.isPending} onChange={event => setConfirmation(event.target.value)} data-testid="settings-confirm-password-input" /></label>
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    <button type="submit" className="button-secondary settings-save-button" disabled={change.isPending} data-testid="settings-change-password-button">{change.isPending ? "Changing…" : "Change password"}</button>
  </form>;
}
