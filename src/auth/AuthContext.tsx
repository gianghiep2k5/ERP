import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { login as apiLogin, getMe } from '../api/auth';
import { TOKEN_KEY } from '../api/client';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type UserRole =
  | 'Warehouse Staff'
  | 'Warehouse Manager'
  | 'Planner'
  | 'Quality Manager'
  | 'Branch Manager';

export interface AuthUser {
  user_id: string;
  username: string;
  role: UserRole;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  /** Returns null on success, error message string on failure. */
  signIn: (username: string, password: string) => Promise<string | null>;
  signOut: () => void;
  /** True only for Warehouse Manager — the sole operational approver. */
  canApprove: boolean;
  /** True only for Planner — can submit forecast reviews. */
  canReviewForecast: boolean;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const signOut = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  // Listen for global 401 unauthorized events emitted by apiClient interceptor
  useEffect(() => {
    const handleUnauthorized = () => {
      signOut();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [signOut]);

  // On mount: restore session from localStorage by calling /api/auth/me
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      getMe(stored)
        .then((me) => {
          setToken(stored);
          setUser({ user_id: me.user_id, username: me.username, role: me.role as UserRole });
        })
        .catch(() => {
          signOut();
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [signOut]);

  const signIn = useCallback(async (username: string, password: string): Promise<string | null> => {
    try {
      const data = await apiLogin(username, password);
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);

      // Fetch full user info (including user_id) from /api/auth/me
      const me = await getMe(data.access_token);
      setUser({ user_id: me.user_id, username: me.username, role: me.role as UserRole });
      return null;
    } catch (err: unknown) {
      signOut();
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Login failed. Please check your credentials.';
      return msg;
    }
  }, [signOut]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      signIn,
      signOut,
      canApprove: user?.role === 'Warehouse Manager',
      canReviewForecast: user?.role === 'Planner',
    }),
    [user, token, isLoading, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
