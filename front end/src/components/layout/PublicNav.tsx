import { Menu, ArrowRight } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { BrandMark } from "@/components/common/BrandMark";

const links = [["How it works", "/how-it-works"], ["Features", "/features"], ["Privacy", "/privacy"], ["About", "/about"]];
export function PublicNav() {
  const [open, setOpen] = useState(false); const location = useLocation(); const { user } = useAuth();
  useEffect(() => { setOpen(false); }, [location.pathname]);
  useEffect(() => { if (!open) return; const close = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); }; document.addEventListener("keydown", close); return () => document.removeEventListener("keydown", close); }, [open]);
  return <header className="public-nav"><BrandMark /><nav className="hidden items-center gap-7 md:flex" aria-label="Public navigation">{links.map(([label, href]) => <Link key={href} to={href} className={location.pathname === href ? "nav-link nav-link-active" : "nav-link"} data-testid={`public-nav-${label.toLowerCase().replaceAll(" ", "-")}`}>{label}</Link>)}</nav><div className="hidden items-center gap-3 md:flex"><Link to={user ? "/app/dashboard" : "/login"} className="nav-login" data-testid="public-nav-login">{user ? "Open workspace" : "Log in"}</Link><Link to="/register" className="button-primary button-small" data-testid="public-nav-create-account">Create account<ArrowRight size={14} /></Link></div><button className="nav-mobile-button md:hidden" type="button" onClick={() => setOpen(!open)} aria-label={open ? "Close navigation" : "Open navigation"} aria-expanded={open} aria-controls="public-mobile-menu" data-testid="public-nav-mobile-toggle"><Menu size={19} /></button>{open && <nav id="public-mobile-menu" className="mobile-menu md:hidden" aria-label="Mobile navigation">{links.map(([label, href]) => <Link key={href} to={href} onClick={() => setOpen(false)} data-testid={`mobile-nav-${label.toLowerCase().replaceAll(" ", "-")}`}>{label}</Link>)}<Link to={user ? "/app/dashboard" : "/login"} onClick={() => setOpen(false)} data-testid="mobile-nav-login">{user ? "Open workspace" : "Log in"}</Link><Link to="/register" className="button-primary button-small" onClick={() => setOpen(false)} data-testid="mobile-nav-create-account">Create account</Link></nav>}</header>;
}
