import { useState } from "react";
import type { ReactNode } from "react";
import { Eye, EyeOff, ArrowLeft, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { appConfig } from "@/config/appConfig";
import { BrandMark } from "@/components/common/BrandMark";
import { authService } from "@/services/authService";

function AuthFrame({ children, title, body }: { children: ReactNode; title: string; body: string }) {
  return <div className="auth-page"><div className="auth-visual"><BrandMark /><div className="auth-visual-copy"><span className="eyebrow"><ShieldCheck size={14} />TrustGraph workspace</span><h1>Read the signal.<br /><span>Keep the trust.</span></h1><p>Bring extension verdicts into a private workspace built around decisions, not message archives.</p><div className="auth-quote"><span className="quote-mark">“</span><p>Only the verdict comes home. The message stays where it was detected.</p></div></div><span className="auth-visual-footer">Result data only</span></div><div className="auth-form-side"><Link to="/" className="auth-back"><ArrowLeft size={15} />Back to home</Link><div className="auth-form-wrap"><span className="eyebrow">{title === "Welcome back" ? "Your workspace" : "Get started"}</span><h2>{title}</h2><p className="auth-subtitle">{body}</p>{children}</div></div></div>;
}
const failureMessage = (error: unknown) => error instanceof Error ? error.message : "The request failed. Please try again.";
function FormError({ error, testId }: { error: string; testId: string }) { return error ? <div className="form-error" role="alert" data-testid={testId}>{error}</div> : null; }

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate(), location = useLocation();
  const [email, setEmail] = useState(""), [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true), [show, setShow] = useState(false);
  const [error, setError] = useState(""), [busy, setBusy] = useState(false);
  const from = typeof location.state?.from === "string" && location.state.from.startsWith("/app/") ? location.state.from : "/app/dashboard";
  return <AuthFrame title="Welcome back" body={appConfig.USE_MOCK ? "Preview the workspace with a valid email and any demo password of at least 8 characters." : "Sign in to review the results your extension has collected."}>
    <form className="auth-form" onSubmit={async event => { event.preventDefault(); setError(""); setBusy(true); try { await login(email.trim(), password, remember); navigate(from, { replace: true }); } catch (failure) { setError(failureMessage(failure)); } finally { setBusy(false); } }}>
      <label>Email address<input type="email" required autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" data-testid="login-email-input" /></label>
      <label>Password<div className="password-input"><input type={show ? "text" : "password"} required minLength={8} autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} placeholder="8+ characters" data-testid="login-password-input" /><button type="button" onClick={() => setShow(!show)} aria-label={show ? "Hide password" : "Show password"} aria-pressed={show} data-testid="login-password-toggle">{show ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
      <div className="form-row"><label className="checkbox-label"><input type="checkbox" checked={remember} onChange={event => setRemember(event.target.checked)} data-testid="login-remember-checkbox" />Remember me</label><Link to="/forgot-password" className="text-link" data-testid="login-forgot-link">Forgot password?</Link></div>
      <FormError error={error} testId="login-error" /><button className="button-primary w-full" type="submit" disabled={busy} data-testid="login-submit-button">{busy ? "Signing in…" : "Sign in"}<ArrowRight size={16} /></button>
    </form><p className="auth-switch">New to TrustGraph? <Link to="/register" data-testid="login-register-link">Create an account</Link></p>
  </AuthFrame>;
}

export function RegisterPage() {
  const { register } = useAuth(); const navigate = useNavigate();
  const [name, setName] = useState(""), [email, setEmail] = useState(""), [password, setPassword] = useState(""), [confirm, setConfirm] = useState("");
  const [error, setError] = useState(""), [busy, setBusy] = useState(false);
  return <AuthFrame title="Create your workspace" body="Start with demo data, then connect your extension when it is ready.">
    <form className="auth-form" onSubmit={async event => { event.preventDefault(); setError(""); if (!name.trim()) { setError("Enter your name."); return; } if (password !== confirm) { setError("Passwords do not match."); return; } setBusy(true); try { await register(name.trim(), email.trim(), password); navigate("/app/dashboard", { replace: true }); } catch (failure) { setError(failureMessage(failure)); } finally { setBusy(false); } }}>
      <label>Your name<input required maxLength={100} autoComplete="name" value={name} onChange={event => setName(event.target.value)} placeholder="Alex Morgan" data-testid="register-name-input" /></label>
      <label>Email address<input required type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" data-testid="register-email-input" /></label>
      <label>Password<input required minLength={8} type="password" autoComplete="new-password" value={password} onChange={event => setPassword(event.target.value)} placeholder="8+ characters" data-testid="register-password-input" /></label>
      <label>Confirm password<input required minLength={8} type="password" autoComplete="new-password" value={confirm} onChange={event => setConfirm(event.target.value)} placeholder="Repeat your password" data-testid="register-confirm-input" /></label>
      <FormError error={error} testId="register-error" /><button className="button-primary w-full" type="submit" disabled={busy} data-testid="register-submit-button">{busy ? "Creating…" : "Create account"}<ArrowRight size={16} /></button>
    </form><p className="auth-switch">Already have an account? <Link to="/login" data-testid="register-login-link">Sign in</Link></p>
  </AuthFrame>;
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState(""), [sent, setSent] = useState(false), [error, setError] = useState(""), [busy, setBusy] = useState(false);
  return <AuthFrame title="Reset your access" body={appConfig.USE_MOCK ? "Preview the password reset flow. No email is sent from this demo." : "Request a reset link for your account email."}>
    {sent ? <div className="success-panel" role="status" data-testid="forgot-success"><CheckCircle2 size={22} /><h3>{appConfig.USE_MOCK ? "Demo reset is ready" : "Check your inbox"}</h3><p>{appConfig.USE_MOCK ? `The demo reset flow is ready for ${email}.` : "If an account exists, a reset link has been sent."}</p>{appConfig.USE_MOCK && <Link to="/reset-password" className="button-primary" data-testid="forgot-reset-link">Continue to reset <ArrowRight size={15} /></Link>}</div> :
      <form className="auth-form" onSubmit={async event => { event.preventDefault(); setError(""); setBusy(true); try { await authService.forgotPassword(email.trim()); setSent(true); } catch (failure) { setError(failureMessage(failure)); } finally { setBusy(false); } }}>
        <label>Email address<input required type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" data-testid="forgot-email-input" /></label>
        <FormError error={error} testId="forgot-error" /><button className="button-primary w-full" type="submit" disabled={busy} data-testid="forgot-submit-button">{busy ? "Preparing…" : appConfig.USE_MOCK ? "Prepare demo reset" : "Send reset link"}<ArrowRight size={16} /></button>
      </form>}
    <p className="auth-switch"><Link to="/login" data-testid="forgot-back-login"><ArrowLeft size={14} />Back to sign in</Link></p>
  </AuthFrame>;
}

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [password, setPassword] = useState(""), [confirm, setConfirm] = useState(""), [error, setError] = useState(""), [busy, setBusy] = useState(false);
  return <AuthFrame title="Choose a new password" body={appConfig.USE_MOCK ? "This previews a reset. Demo sign-in continues to accept any password of at least 8 characters." : "Use at least 8 characters to protect your workspace."}>
    <form className="auth-form" onSubmit={async event => { event.preventDefault(); setError(""); if (password !== confirm) { setError("Passwords do not match."); return; } setBusy(true); try { await authService.resetPassword(password); navigate("/login", { replace: true }); } catch (failure) { setError(failureMessage(failure)); } finally { setBusy(false); } }}>
      <label>New password<input required minLength={8} type="password" autoComplete="new-password" value={password} onChange={event => setPassword(event.target.value)} placeholder="8+ characters" data-testid="reset-password-input" /></label>
      <label>Confirm password<input required minLength={8} type="password" autoComplete="new-password" value={confirm} onChange={event => setConfirm(event.target.value)} placeholder="Repeat your password" data-testid="reset-confirm-input" /></label>
      <FormError error={error} testId="reset-error" /><button className="button-primary w-full" type="submit" disabled={busy} data-testid="reset-submit-button">{busy ? "Saving…" : appConfig.USE_MOCK ? "Finish demo reset" : "Save password"}<ArrowRight size={16} /></button>
    </form>
  </AuthFrame>;
}
