import { useState } from "react";
import type { ReactNode } from "react";
import { ArrowLeft, ArrowRight, LockKeyhole } from "lucide-react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { BrandMark } from "@/components/common/BrandMark";
import { NetworkBackdrop } from "@/components/common/NetworkBackdrop";
import { LoginForm } from "@/components/auth/LoginForm";
import { PasswordInput } from "@/components/auth/PasswordInput";
import { validateLogin } from "@/lib/authValidation";

function AuthFrame({ children, title, body }: { children: ReactNode; title: string; body: string }) {
  return <NetworkBackdrop className="login-page">
    <Link to="/" className="auth-back login-back"><ArrowLeft size={15} />Back to home</Link>
    <main className="panel login-card">
      <div className="login-brand"><BrandMark /></div>
      <span className="eyebrow">Your digital trust workspace</span>
      <h1>{title}</h1><p className="auth-subtitle">{body}</p>{children}
      <p className="login-security"><LockKeyhole size={14} />Secure access to your digital trust intelligence.</p>
    </main>
  </NetworkBackdrop>;
}
function AuthLoading() { return <div className="loading-screen" role="status"><span className="loading-spinner" />Checking your session…</div>; }

export function LoginPage() {
  const { user, loading } = useAuth();
  if (loading) return <AuthLoading />;
  if (user) return <Navigate to="/dashboard" replace />;
  return <AuthFrame title="Welcome back" body="Sign in to continue to TrustGraph">
    <LoginForm /><p className="auth-switch">Don't have an account? <Link to="/signup" data-testid="login-register-link">Create account</Link></p>
  </AuthFrame>;
}

export function RegisterPage() {
  const { register, user, loading } = useAuth();
  const [name, setName] = useState(""), [email, setEmail] = useState("");
  const [password, setPassword] = useState(""), [confirm, setConfirm] = useState("");
  const [error, setError] = useState(""), [busy, setBusy] = useState(false);
  if (loading) return <AuthLoading />;
  if (user) return <Navigate to="/dashboard" replace />;
  return <AuthFrame title="Create your account" body="One place for your browser verdicts and trust insights.">
    <form className="auth-form" noValidate aria-busy={busy} onSubmit={async event => {
      event.preventDefault(); if (busy) return;
      const invalid = validateLogin(email, password);
      const message = !name.trim() ? "Enter your name." : invalid.email || invalid.password ||
        (password.length < 15 || !password.trim() ? "Use a passphrase of at least 15 characters." : "") ||
        (password !== confirm ? "Passwords do not match." : "");
      setError(message); if (message) return;
      setBusy(true);
      try { await register(name.trim(), email.trim(), password); setPassword(""); setConfirm(""); }
      catch (failure) { setError(failure instanceof Error ? failure.message : "Could not create your account."); }
      finally { setBusy(false); }
    }}>
      <label htmlFor="signup-name">Your name<input id="signup-name" required disabled={busy} maxLength={100} autoComplete="name" value={name} onChange={event => setName(event.target.value)} data-testid="register-name-input" /></label>
      <label htmlFor="signup-email">Email address<input id="signup-email" required disabled={busy} maxLength={254} type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" data-testid="register-email-input" /></label>
      <div><label htmlFor="signup-password">Password</label><PasswordInput id="signup-password" value={password} onChange={setPassword} disabled={busy} autoComplete="new-password" /><p className="input-help" id="signup-password-help">Use a passphrase of 15–128 characters.</p></div>
      <label htmlFor="signup-confirm">Confirm password<input id="signup-confirm" required disabled={busy} maxLength={128} type="password" autoComplete="new-password" value={confirm} onChange={event => setConfirm(event.target.value)} data-testid="register-confirm-input" /></label>
      {error && <div className="form-error" role="alert" data-testid="register-error">{error}</div>}
      <button className="button-primary w-full" type="submit" disabled={busy} data-testid="register-submit-button">{busy ? "Creating account…" : "Create account"}<ArrowRight size={16} /></button>
    </form><p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
  </AuthFrame>;
}

export function ForgotPasswordPage() {
  return <AuthFrame title="Account recovery" body="Password reset email is not configured yet.">
    <p className="empty-period-note">Contact your TrustGraph administrator for recovery. No email has been sent, and this page cannot change your password.</p>
    <p className="auth-switch"><Link to="/login">Back to sign in</Link></p>
  </AuthFrame>;
}
export function ResetPasswordPage() { return <ForgotPasswordPage />; }
