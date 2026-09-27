// src/auth.jsx - who is logged in, available everywhere through useAuth()
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { get, getToken, request, setToken } from "./api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// Each role has its own home page
export const homeFor = (role) => (role === "admin" ? "/admin" : role === "driver" ? "/driver" : "/me");

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // {id, full_name, role, customer, ...} or null
  const [loading, setLoading] = useState(!!getToken());

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  // Ask the backend who the token belongs to
  const refresh = useCallback(async () => {
    try {
      setUser(await get("/auth/me"));
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    if (getToken()) refresh();
  }, [refresh]);

  useEffect(() => {
    window.addEventListener("auth-expired", logout);
    return () => window.removeEventListener("auth-expired", logout);
  }, [logout]);

  // The backend login expects a form with "username" (= phone number) and "password"
  async function login(phone, password) {
    const body = new URLSearchParams({ username: phone, password });
    const { access_token } = await request("/auth/login", { method: "POST", body });
    setToken(access_token);
    await refresh();
  }

  return <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>{children}</AuthContext.Provider>;
}
