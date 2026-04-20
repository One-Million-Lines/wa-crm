import React, { createContext, useContext, useState, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE;

type AuthState = {
  token: string | null;
  email: string | null;
  userId: string | null;
  role: string | null;
  name: string | null;
};

type AuthContextType = AuthState & {
  requestChallenge: (email: string) => Promise<string>;
  login: (challengeId: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextType | null>(null);

const STORAGE_KEY = 'wacrm_auth';

function loadAuth(): AuthState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return { token: null, email: null, userId: null, role: null, name: null };
}

function saveAuth(state: AuthState) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>(loadAuth);

  const setAndPersistAuth = useCallback((state: AuthState) => {
    saveAuth(state);
    setAuth(state);
  }, []);

  const requestChallenge = useCallback(async (email: string): Promise<string> => {
    const res = await fetch(`${API_BASE}/auth/challenge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) throw new Error('Failed to request challenge');
    const data = await res.json();
    return data.challengeId;
  }, []);

  const login = useCallback(async (challengeId: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ challengeId, password }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || 'Invalid credentials');
    }
    const data = await res.json();
    setAndPersistAuth({
      token: data.token,
      email: data.email,
      userId: data.userId,
      role: data.role || 'agent',
      name: data.name || data.email,
    });
  }, [setAndPersistAuth]);

  const logout = useCallback(() => {
    setAndPersistAuth({ token: null, email: null, userId: null, role: null, name: null });
    localStorage.removeItem(STORAGE_KEY);
  }, [setAndPersistAuth]);

  return (
    <AuthContext.Provider
      value={{
        ...auth,
        requestChallenge,
        login,
        logout,
        isAuthenticated: !!auth.token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
