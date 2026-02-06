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
  idToken: string | null;
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
  const [idToken, setIdToken] = useState<string | null>(null);
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
    setIdToken(token); // In mock mode, same token for both
    sessionStorage.setItem("selectedPlan", plan);
    sessionStorage.setItem("mockUser", JSON.stringify(mockUser));
    sessionStorage.setItem("mockToken", token);
  }, []);

  const refreshSession = useCallback(async () => {
    console.log("refreshSession: Starting...", { isMockAuth });

    // Mock auth mode - check sessionStorage for mock user
    if (isMockAuth) {
      const storedUser = sessionStorage.getItem("mockUser");
      const storedToken = sessionStorage.getItem("mockToken");
      if (storedUser && storedToken) {
        const parsed = JSON.parse(storedUser);
        setUser(parsed);
        setAccessToken(storedToken);
        setIdToken(storedToken); // In mock mode, same token for both
      } else {
        setUser(null);
        setAccessToken(null);
        setIdToken(null);
      }
      return;
    }

    // Real Cognito auth
    try {
      console.log("refreshSession: Fetching auth session...");
      const session = await fetchAuthSession();
      console.log("refreshSession: Session result:", {
        hasTokens: !!session.tokens,
        hasAccessToken: !!session.tokens?.accessToken,
        hasIdToken: !!session.tokens?.idToken,
      });
      const tokens = session.tokens;

      if (tokens?.accessToken) {
        console.log("refreshSession: Got access token");
        setAccessToken(tokens.accessToken.toString());

        // Store ID token for API calls (contains email claim)
        if (tokens.idToken) {
          setIdToken(tokens.idToken.toString());
        }

        // Try to get user info from ID token first (more reliable)
        // ID token contains user claims without needing additional API calls
        let userEmail = "";
        let userSub = "";
        let emailVerified = false;

        if (tokens.idToken) {
          // Parse ID token payload (it's a JWT)
          const idTokenPayload = tokens.idToken.payload;
          console.log("refreshSession: ID token payload:", idTokenPayload);
          userEmail = (idTokenPayload.email as string) || "";
          userSub = (idTokenPayload.sub as string) || "";
          emailVerified = idTokenPayload.email_verified === true;
        }

        // Fall back to getCurrentUser and fetchUserAttributes if needed
        if (!userSub) {
          try {
            const currentUser = await getCurrentUser();
            console.log("refreshSession: Current user:", currentUser);
            userSub = currentUser.userId;
          } catch (err) {
            console.warn("refreshSession: Could not get current user:", err);
          }
        }

        if (!userEmail) {
          try {
            const attributes = await fetchUserAttributes();
            console.log("refreshSession: User attributes:", attributes);
            userEmail = attributes.email || "";
            emailVerified = attributes.email_verified === "true";
          } catch (err) {
            console.warn("refreshSession: Could not fetch user attributes:", err);
            // This is OK - we might not have the scopes, but we have the token
          }
        }

        if (userSub) {
          setUser({
            sub: userSub,
            email: userEmail,
            emailVerified,
          });
          console.log("refreshSession: User set successfully", { userSub, userEmail });
        } else {
          console.log("refreshSession: No user sub found, clearing user");
          setUser(null);
          setAccessToken(null);
          setIdToken(null);
        }
      } else {
        console.log("refreshSession: No access token found");
        setUser(null);
        setAccessToken(null);
        setIdToken(null);
      }
    } catch (error) {
      console.error("refreshSession: Error:", error);
      setUser(null);
      setAccessToken(null);
      setIdToken(null);
    }
  }, []);

  // Initialize auth state and listen for auth events
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);

      // Check if we're handling an OAuth callback (code in URL)
      const urlParams = new URLSearchParams(window.location.search);
      const hasAuthCode = urlParams.has("code");

      if (hasAuthCode && !isMockAuth) {
        console.log("initAuth: OAuth callback detected, code in URL");
        // When we have a code, Amplify should automatically exchange it
        // Give it a moment to process, then refresh session
        await new Promise((resolve) => setTimeout(resolve, 500));
      }

      await refreshSession();
      setIsLoading(false);
    };

    initAuth();

    // Skip Hub listener in mock mode
    if (isMockAuth) return;

    // Listen for auth events from Cognito Hosted UI
    console.log("Setting up Hub listener for auth events...");
    const hubListener = Hub.listen("auth", async ({ payload }) => {
      console.log("Hub auth event received:", payload.event, payload);
      switch (payload.event) {
        case "signInWithRedirect":
          // User successfully signed in via Hosted UI
          console.log("Hub: signInWithRedirect event - refreshing session");
          await refreshSession();
          break;
        case "signInWithRedirect_failure":
          // Sign in failed
          console.error("Hub: Sign in failed:", payload.data);
          break;
        case "signedOut":
          console.log("Hub: User signed out");
          setUser(null);
          setAccessToken(null);
          setIdToken(null);
          break;
        case "tokenRefresh":
          console.log("Hub: Token refreshed");
          await refreshSession();
          break;
        case "tokenRefresh_failure":
          console.error("Hub: Token refresh failed:", payload.data);
          setUser(null);
          setAccessToken(null);
          setIdToken(null);
          break;
        default:
          console.log("Hub: Unhandled auth event:", payload.event);
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
    console.log("signInWithHostedUI: Starting redirect to Cognito...");
    try {
      await signInWithRedirect();
      // This line should never be reached as signInWithRedirect triggers a browser redirect
      console.log("signInWithHostedUI: Redirect completed (unexpected)");
    } catch (error: unknown) {
      console.error("signInWithHostedUI: Error during redirect:", error);
      // Handle "already signed in" error by refreshing session
      if (error instanceof Error && error.message.includes("already")) {
        console.log("signInWithHostedUI: User already signed in, refreshing session");
        await refreshSession();
        // Throw a special error so caller knows to redirect
        throw new Error("ALREADY_SIGNED_IN");
      }
      throw error;
    }
  };

  const logout = async () => {
    if (isMockAuth) {
      sessionStorage.removeItem("mockUser");
      sessionStorage.removeItem("mockToken");
      sessionStorage.removeItem("selectedPlan");
      setUser(null);
      setAccessToken(null);
      setIdToken(null);
      return;
    }
    await signOut();
    setUser(null);
    setAccessToken(null);
    setIdToken(null);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: Boolean(user),
    accessToken,
    idToken,
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
