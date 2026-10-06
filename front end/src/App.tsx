import { useEffect } from "react";
import { AnalyzePage } from "@/pages/AnalyzePage";
import { Link, Navigate, Outlet, Route, Routes, useLocation, useParams } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { Home } from "@/pages/PublicPage";
import { ContactPage, PublicPage } from "@/pages/PublicPage";
import { ForgotPasswordPage, LoginPage, RegisterPage, ResetPasswordPage } from "@/pages/AuthPages";
import { AnalyticsPage, DashboardPage, DetectionDetailPage, DetectionsPage, ProfilePage, SettingsPage } from "@/pages/AppPages";

function ProtectedLayout() {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="loading-screen"><span className="loading-spinner" />Loading TrustGraph…</div>;
  // This frontend guard is for user experience only; real authorization belongs to the backend.
  return user ? <AppShell><Outlet /></AppShell> : <Navigate to="/login" state={{ from: location.pathname + location.search }} replace />;
}

function LegacyResultRedirect() {
  const { id = "" } = useParams();
  return <Navigate to={`/app/detections/${encodeURIComponent(id)}`} replace />;
}

function NotFound() {
  const { user } = useAuth();
  return <main className="public-narrow"><span className="eyebrow">404 · Page not found</span><h1>This page isn’t here.</h1><p className="public-lede">Check the address or return to your workspace.</p><Link className="button-primary" to={user ? "/app/dashboard" : "/"}>Return to {user ? "dashboard" : "home"}</Link></main>;
}

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/how-it-works" element={<PublicPage path="/how-it-works" />} />
      <Route path="/features" element={<PublicPage path="/features" />} />
      <Route path="/about" element={<PublicPage path="/about" />} />
      <Route path="/privacy" element={<PublicPage path="/privacy" />} />
      <Route path="/contact" element={<ContactPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<RegisterPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="/results/:id" element={<LegacyResultRedirect />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/app" element={<ProtectedLayout />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="detections" element={<DetectionsPage />} />
        <Route path="detections/:id" element={<DetectionDetailPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="analyze" element={<AnalyzePage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
