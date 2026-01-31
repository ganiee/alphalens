"use client";

import {
  fetchAuthSession,
  fetchUserAttributes,
  getCurrentUser,
  signInWithRedirect,
  signOut,
} from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export interface AuthUser {
  sub: string;
  email: string;
  emailVerified: boolean;
}

export interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  accessToken: string | null;
  signInWithHostedUI: () => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
  mockLogin?: (email: string, plan: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

const isMockAuth = process.env.NEXT_PUBLIC_AUTH_MODE === "mock";

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Mock login function for local testing
  // Uses predefined tokens that backend MockAuthVerifier accepts
  const mockLogin = useCallback((email: string, plan: string) => {
    // Backend expects these specific tokens:
    // - "test-user-token" for free users
    // - "test-pro-token" for pro users
    // - "test-admin-token" for admin users
    const token = plan === "pro" ? "test-pro-token" : "test-user-token";
    const sub = plan === "pro" ? "test-pro-789" : "test-user-123";

    const mockUser: AuthUser = {
      sub,
      email,
      emailVerified: true,
    };
    setUser(mockUser);
    setAccessToken(token);
    sessionStorage.setItem("selectedPlan", plan);
    sessionStorage.setItem("mockUser", JSON.stringify(mockUser));
    sessionStorage.setItem("mockToken", token);
  }, []);

  const refreshSession = useCallback(async () => {
    // Mock auth mode - check sessionStorage for mock user
    if (isMockAuth) {
      const storedUser = sessionStorage.getItem("mockUser");
      const storedToken = sessionStorage.getItem("mockToken");
      if (storedUser && storedToken) {
        const parsed = JSON.parse(storedUser);
        setUser(parsed);
        setAccessToken(storedToken);
      } else {
        setUser(null);
        setAccessToken(null);
      }
      return;
    }

    // Real Cognito auth
    try {
      const session = await fetchAuthSession();
      const tokens = session.tokens;

      if (tokens?.accessToken) {
        setAccessToken(tokens.accessToken.toString());

        const currentUser = await getCurrentUser();
        const attributes = await fetchUserAttributes();

        setUser({
          sub: currentUser.userId,
          email: attributes.email || "",
          emailVerified: attributes.email_verified === "true",
        });
      } else {
        setUser(null);
        setAccessToken(null);
      }
    } catch {
      setUser(null);
      setAccessToken(null);
    }
  }, []);

  // Initialize auth state and listen for auth events
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      await refreshSession();
      setIsLoading(false);
    };

    initAuth();

    // Skip Hub listener in mock mode
    if (isMockAuth) return;

    // Listen for auth events from Cognito Hosted UI
    const hubListener = Hub.listen("auth", async ({ payload }) => {
      switch (payload.event) {
        case "signInWithRedirect":
          // User successfully signed in via Hosted UI
          await refreshSession();
          break;
        case "signInWithRedirect_failure":
          // Sign in failed
          console.error("Sign in failed:", payload.data);
          break;
        case "signedOut":
          setUser(null);
          setAccessToken(null);
          break;
      }
    });

    return () => hubListener();
  }, [refreshSession]);

  const signInWithHostedUI = async () => {
    if (isMockAuth) {
      // In mock mode, this is handled by the login page directly
      return;
    }
    // Redirect to Cognito Hosted UI
    // This handles both sign-in and sign-up
    await signInWithRedirect();
  };

  const logout = async () => {
    if (isMockAuth) {
      sessionStorage.removeItem("mockUser");
      sessionStorage.removeItem("mockToken");
      sessionStorage.removeItem("selectedPlan");
      setUser(null);
      setAccessToken(null);
      return;
    }
    await signOut();
    setUser(null);
    setAccessToken(null);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: Boolean(user),
    accessToken,
    signInWithHostedUI,
    logout,
    refreshSession,
    ...(isMockAuth && { mockLogin }),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export { isMockAuth };
