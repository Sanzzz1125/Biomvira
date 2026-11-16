import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { authApi } from '../services/accounts';
import { ApiError } from '../services/http';
import { Role, User } from '../types';

export const SIGNED_IN_HINT = 'nl_signed_in';

/** Whether this browser was signed in last time; used only to choose what the header shows while the session loads. */
export function wasSignedIn(): boolean {
  try {
    return window.localStorage.getItem(SIGNED_IN_HINT) === '1';
  } catch {
    return false;
  }
}

interface AuthContextValue {
  user: User | null;
  ready: boolean;
  isStaff: boolean;
  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<User>;
  register: (name: string, email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const isUser = (value: unknown): value is User =>
  !!value && typeof (value as User).email === 'string' && typeof (value as User).role === 'string';

export const AuthProvider: React.FC<{ children: React.ReactNode; onSignedOut?: () => void }> = ({
  children,
  onSignedOut,
}) => {
  const [user, setUserState] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const userRef = useRef<User | null>(null);
  const signedOutRef = useRef(onSignedOut);
  signedOutRef.current = onSignedOut;

  // Clears any on-screen medical results when the signed-in person changes or signs out.
  const setUser = useCallback((next: User | null) => {
    const previous = userRef.current;
    if (previous && (!next || next.id !== previous.id)) signedOutRef.current?.();
    userRef.current = next;
    setUserState(next);
    // Remember only whether someone was signed in (no personal data), so the header can show the right
    // buttons immediately next time instead of waiting for the server.
    try {
      if (next) window.localStorage.setItem(SIGNED_IN_HINT, '1');
      else window.localStorage.removeItem(SIGNED_IN_HINT);
    } catch {
      /* storage unavailable: the header simply waits for the server */
    }
  }, []);

  const refresh = useCallback(async () => {
    for (let attempt = 0; ; attempt++) {
      try {
        const { user: me } = await authApi.session();
        setUser(isUser(me) ? me : null);
        break;
      } catch (err) {
        // The free API server can be waking up or briefly unreachable. Retry those failures a few
        // times so a signed-in person isn't shown as signed out (and bounced to login) by a blip.
        const status = err instanceof ApiError ? err.status : 0;
        if ((status === 0 || status >= 500) && attempt < 3) {
          await new Promise((resolve) => window.setTimeout(resolve, 4000));
          continue;
        }
        setUser(null);
        break;
      }
    }
    setReady(true);
  }, [setUser]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      const me = await authApi.login(email, password);
      setUser(me);
      return me;
    },
    [setUser]
  );

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      const me = await authApi.register(name, email, password);
      setUser(me);
      return me;
    },
    [setUser]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  }, [setUser]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      ready,
      isStaff: user?.role === 'admin' || user?.role === 'owner',
      setUser,
      login,
      register,
      logout,
      refresh,
    }),
    [user, ready, setUser, login, register, logout, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}

export const ROLE_LABEL: Record<Role, string> = { owner: 'Owner', admin: 'Admin', user: 'User' };
