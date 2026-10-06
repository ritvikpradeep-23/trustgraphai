import { useEffect, useMemo, useState } from "react";
import { AuthContext } from "./authState";
export { useAuth } from "./authState";
import { authService } from "@/services/authService";
import { queryClient } from "@/lib/queryClient";
import type { User } from "@/types/trustgraph";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    authService.me().then(next => { if (active) setUser(next); }).catch(() => { if (active) setUser(null); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  const value = useMemo(() => ({
    user, loading,
    login: async (email: string, password: string, remember = false) => { const next = await authService.login(email, password, remember); queryClient.clear(); setUser(next); return next; },
    register: async (name: string, email: string, password: string) => { const next = await authService.register(name, email, password); queryClient.clear(); setUser(next); return next; },
    logout: async () => { await authService.logout(); queryClient.clear(); setUser(null); },
    deleteAccount: async () => { await authService.deleteAccount(); queryClient.clear(); setUser(null); },
    refreshUser: async () => { setUser(await authService.me()); },
  }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
