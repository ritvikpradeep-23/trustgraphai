import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { BarChart3, ChevronLeft, ChevronRight, FileClock, LayoutDashboard, LogOut, Menu, Settings, UserRound, X } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { appConfig } from "@/config/appConfig";
import { BrandMark } from "@/components/common/BrandMark";
import { DemoBanner } from "@/components/common/DemoBanner";
import { DevPanel } from "@/components/common/DevPanel";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { detectionService } from "@/services/detectionService";
import { useQueryClient } from "@tanstack/react-query";

const navigation = [{ label: "Analyze", href: "/app/analyze", icon: BarChart3 }, { label: "Overview", href: "/app/dashboard", icon: LayoutDashboard }, { label: "Detection history", href: "/app/detections", icon: FileClock }, { label: "Analytics", href: "/app/analytics", icon: BarChart3 }, { label: "Profile", href: "/app/profile", icon: UserRound }, { label: "Settings", href: "/app/settings", icon: Settings }];

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);
  const [busy, setBusy] = useState(false);
  const sidebar = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  useEffect(() => {
    const media = window.matchMedia("(max-width: 760px)");
    const resize = () => { if (!media.matches) setMobileOpen(false); };
    media.addEventListener("change", resize);
    return () => media.removeEventListener("change", resize);
  }, []);
  useEffect(() => {
    if (!mobileOpen) return;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    sidebar.current?.querySelector<HTMLButtonElement>(".sidebar-mobile-close")?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileOpen(false);
      if (event.key === "Tab") {
        const elements = [...(sidebar.current?.querySelectorAll<HTMLElement>("a, button") ?? [])].filter(element => element.getClientRects().length);
        const first = elements[0], last = elements.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener("keydown", keydown);
    return () => { document.body.style.overflow = overflow; document.removeEventListener("keydown", keydown); menuButton.current?.focus(); };
  }, [mobileOpen]);
  const clearDemo = async () => {
    setBusy(true);
    try { await detectionService.clear(); await queryClient.invalidateQueries(); setConfirmClear(false); toast.success("Demo history cleared. Use Mock preview to restore the seed."); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Could not clear history."); }
    finally { setBusy(false); }
  };
  return <div className="app-frame">
    {mobileOpen && <button className="sidebar-backdrop" aria-label="Close navigation" tabIndex={-1} onClick={() => setMobileOpen(false)} />}
    <aside ref={sidebar} id="workspace-sidebar" className={`app-sidebar ${collapsed ? "app-sidebar-collapsed" : ""} ${mobileOpen ? "app-sidebar-mobile-open" : ""}`}>
      <div className="sidebar-top"><BrandMark /><button className="sidebar-collapse" type="button" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} data-testid="sidebar-collapse-button">{collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}</button><button className="sidebar-mobile-close" type="button" aria-label="Close navigation" onClick={() => setMobileOpen(false)} data-testid="sidebar-mobile-close"><X size={18} /></button></div>
      <div className="sidebar-label">Workspace</div>
      <nav className="sidebar-nav" aria-label="App navigation">{navigation.map(({ label, href, icon: Icon }) => <NavLink key={href} to={href} aria-label={label} title={collapsed ? label : undefined} onClick={() => setMobileOpen(false)} className={({ isActive }) => `sidebar-link ${isActive ? "sidebar-link-active" : ""}`} data-testid={`sidebar-link-${label.toLowerCase().replaceAll(" ", "-")}`}><Icon size={18} /><span>{label}</span></NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-extension"><span className="live-dot" /><span>{appConfig.USE_MOCK ? "Extension companion" : "Local backend workspace"}</span></div>{appConfig.USE_MOCK && <button className="sidebar-logout" type="button" aria-label="Sign out" disabled={busy} onClick={async () => { setBusy(true); try { await logout(); navigate("/"); } catch { toast.error("Could not sign out. Try again."); } finally { setBusy(false); } }} data-testid="sidebar-logout-button"><LogOut size={17} /><span>Sign out</span></button>}</div>
    </aside>
    <main inert={mobileOpen} className={`app-main ${collapsed ? "app-main-expanded" : ""}`}>
      <div className="app-topbar"><button ref={menuButton} type="button" className="mobile-menu-button" aria-label="Open navigation" aria-expanded={mobileOpen} aria-controls="workspace-sidebar" onClick={() => setMobileOpen(true)} data-testid="sidebar-mobile-open"><Menu size={19} /></button><div className="topbar-title">TrustGraph <span>/ Workspace</span></div><div className="topbar-user"><div className="avatar">{user?.name.slice(0, 1) || "A"}</div><span className="hidden sm:inline" data-testid="topbar-user-name">{user?.name}</span></div></div>
      {appConfig.USE_MOCK ? <DemoBanner onClear={() => setConfirmClear(true)} /> : <div className="demo-banner" role="status">Your account workspace · Pair your extension in Settings · Unknown is not safe</div>}
      <div className="app-content">{children}</div>
    </main>
    {appConfig.USE_MOCK && <DevPanel />}
    {confirmClear && <ConfirmDialog title="Clear demo history?" description="Remove every demo result from this browser. You can restore the sample data from Mock preview." confirmLabel="Clear history" busy={busy} onClose={() => setConfirmClear(false)} onConfirm={() => void clearDemo()} />}
  </div>;
}
