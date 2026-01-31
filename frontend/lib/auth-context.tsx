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
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshSession = useCallback(async () => {
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
    // Redirect to Cognito Hosted UI
    // This handles both sign-in and sign-up
    await signInWithRedirect();
  };

  const logout = async () => {
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
