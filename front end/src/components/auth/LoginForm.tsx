import { useRef, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { validateLogin } from "@/lib/authValidation";
import type { LoginErrors } from "@/lib/authValidation";
import { PasswordInput } from "./PasswordInput";
export function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState(""), [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false), [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState<LoginErrors>({}), [serverError, setServerError] = useState("");
  const inFlight = useRef(false);
  return <form className="auth-form" noValidate aria-busy={busy} onSubmit={async event => {
    event.preventDefault();
    if (inFlight.current) return;
    const next = validateLogin(email, password);
    setErrors(next); setServerError("");
    if (Object.values(next).some(Boolean)) {
      document.getElementById(next.email ? "login-email" : "login-password")?.focus();
      return;
    }
    inFlight.current = true; setBusy(true);
    try { await login(email, password, remember); setPassword(""); navigate("/dashboard", { replace: true }); }
    catch (error) { setServerError(error instanceof Error ? error.message : "Sign-in failed. Please try again."); }
    finally { inFlight.current = false; setBusy(false); }
  }}>
    <div><label htmlFor="login-email">Email Address</label>
      <input id="login-email" name="email" type="email" required autoComplete="email" maxLength={254}
        value={email} onChange={event => { setEmail(event.target.value); setErrors(current => ({ ...current, email: undefined })); }}
        disabled={busy} placeholder="you@example.com" aria-invalid={Boolean(errors.email)}
        aria-describedby={errors.email ? "login-email-error" : undefined} data-testid="login-email-input" />
      {errors.email && <p className="field-error" id="login-email-error">{errors.email}</p>}
    </div>
    <div><label htmlFor="login-password">Password</label>
      <PasswordInput id="login-password" value={password} onChange={value => { setPassword(value); setErrors(current => ({ ...current, password: undefined })); }}
        disabled={busy} error={errors.password} />
      {errors.password && <p className="field-error" id="login-password-error">{errors.password}</p>}
    </div>
    <div className="form-row"><label className="checkbox-label"><input type="checkbox" checked={remember}
      onChange={event => setRemember(event.target.checked)} disabled={busy} data-testid="login-remember-checkbox" />Remember me</label>
      <Link to="/forgot-password" className="text-link" data-testid="login-forgot-link">Forgot password?</Link></div>
    {serverError && <div className="form-error" role="alert" data-testid="login-error">{serverError}</div>}
    <button className="button-primary w-full" type="submit" disabled={busy} data-testid="login-submit-button">
      {busy ? <><span className="loading-spinner login-spinner" aria-hidden="true" />Signing in…</> : <>Sign In<ArrowRight size={16} /></>}
    </button>
  </form>;
}
