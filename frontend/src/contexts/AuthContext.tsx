import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { authApi, type AuthResponse, type LoginParams, type RegisterParams } from "../api/auth";

interface AuthContextType {
  user: AuthResponse | null;
  loading: boolean;
  login: (params: LoginParams) => Promise<AuthResponse>;
  register: (params: RegisterParams) => Promise<AuthResponse>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthResponse | null>(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      localStorage.setItem("user", JSON.stringify(user));
    } else {
      localStorage.removeItem("user");
    }
  }, [user]);

  const login = useCallback(async (params: LoginParams) => {
    setLoading(true);
    try {
      const u = await authApi.login(params);
      setUser(u);
      return u;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (params: RegisterParams) => {
    setLoading(true);
    try {
      const u = await authApi.register(params);
      setUser(u);
      return u;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
