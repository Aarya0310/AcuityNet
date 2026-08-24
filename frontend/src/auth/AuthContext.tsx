import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { clearSession, getCurrentUser, login, logout, type AuthUser } from "../api/client";

type AuthState = { user: AuthUser | null; loading: boolean; error: string | null; signIn: (username: string, password: string) => Promise<void>; signOut: () => Promise<void> };
const AuthContext = createContext<AuthState | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  useEffect(() => { getCurrentUser().then(setUser).catch(() => { clearSession(); setUser(null); }).finally(() => setLoading(false)); }, []);
  async function signIn(username: string, password: string) { const session = await login(username, password); setUser(session.user); setError(null); }
  async function signOut() { await logout(); setUser(null); }
  return <AuthContext.Provider value={{ user, loading, error, signIn, signOut }}>{children}</AuthContext.Provider>;
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("AuthProvider required"); return value; }