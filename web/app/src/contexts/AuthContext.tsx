import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const TOKEN_KEY = 'holkos_token';

interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  user: { username: string } | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  updateSession: (token: string, username: string) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<{ username: string } | null>(null);

  const getToken = useCallback(() => localStorage.getItem(TOKEN_KEY), []);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    const token = getToken();
    if (!token) return false;
    try {
      const { data } = await api.post<{ access_token: string }>('/auth/refresh', {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (data?.access_token) {
        localStorage.setItem(TOKEN_KEY, data.access_token);
        return true;
      }
    } catch {
      // Token invalid or expired
    }
    return false;
  }, [getToken]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setIsAuthenticated(false);
    setUser(null);
  }, []);

  const updateSession = useCallback((token: string, username: string) => {
    localStorage.setItem(TOKEN_KEY, token);
    setIsAuthenticated(true);
    setUser({ username });
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { data } = await api.post<{ access_token: string }>('/auth/login', { username, password });
    if (data?.access_token) {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setIsAuthenticated(true);
      setUser({ username });
    } else {
      throw new Error('Nuk u mor token.');
    }
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    // Basic JWT decode to check expiry (client-side, not for security)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload?.exp ? payload.exp * 1000 : 0;
      if (exp > Date.now()) {
        setIsAuthenticated(true);
        setUser({ username: payload?.sub || 'user' });
      } else {
        refreshToken().then((ok) => {
          if (ok) {
            const t = localStorage.getItem(TOKEN_KEY);
            const p = t ? JSON.parse(atob(t.split('.')[1])) : null;
            setIsAuthenticated(true);
            setUser({ username: p?.sub || 'user' });
          } else {
            logout();
          }
          setLoading(false);
        }).catch(() => {
          logout();
          setLoading(false);
        });
        return;
      }
    } catch {
      logout();
    }
    setLoading(false);
  }, [getToken, logout, refreshToken]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading, user, login, logout, refreshToken, updateSession }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
