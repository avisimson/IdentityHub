import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { User } from "@/types";
import {
  setAccessToken,
  setOnUserUpdate,
  clearAuth,
} from "@/api/client";
import { refresh as silentRefresh, logout as apiLogout } from "@/api/authApi";

interface AuthContextValue {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  login: (accessToken: string, user: User) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setOnUserUpdate(setUser);
    return () => setOnUserUpdate(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function attemptRefresh() {
      try {
        const data = await silentRefresh();
        if (cancelled) return;
        setAccessToken(data.access_token);
        setToken(data.access_token);
        setUser(data.user);
      } catch {
        // Refresh failed — user stays unauthenticated
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    attemptRefresh();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback((accessToken: string, user: User) => {
    setAccessToken(accessToken);
    setToken(accessToken);
    setUser(user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      clearAuth();
      setToken(null);
      setUser(null);
      window.location.href = "/login";
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, accessToken: token, isLoading, login, logout }),
    [user, token, isLoading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
