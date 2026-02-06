"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";

import { useAuth, isMockAuth } from "@/lib/auth-context";

function HomeContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const hasProcessedCallback = useRef(false);

  useEffect(() => {
    // Check if we have an auth code in the URL (OAuth callback)
    const authCode = searchParams.get("code");
    const hasAuthCallback = Boolean(authCode) && !isMockAuth;

    console.log("Home page state:", {
      isLoading,
      isAuthenticated,
      hasAuthCallback,
      authCode: authCode ? "present" : "none",
      isMockAuth,
      hasProcessedCallback: hasProcessedCallback.current,
    });

    // If we have an auth callback and haven't processed it yet, wait for auth to complete
    if (hasAuthCallback && !hasProcessedCallback.current) {
      hasProcessedCallback.current = true;
      console.log("Auth callback detected, waiting for Amplify to process...");
      // Don't redirect yet - let the auth context process the callback
      // The isLoading state will handle this
      return;
    }

    // Wait for auth loading to complete
    if (isLoading) {
      console.log("Auth still loading, waiting...");
      return;
    }

    // Auth loading complete - redirect based on state
    if (isAuthenticated) {
      console.log("User authenticated, redirecting to dashboard");
      router.replace("/dashboard");
    } else {
      console.log("User not authenticated, redirecting to login");
      // Clear the URL params before redirecting to avoid loops
      if (hasAuthCallback) {
        window.history.replaceState({}, "", "/");
      }
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router, searchParams]);

  // Show loading while checking auth state
  const authCode = searchParams.get("code");
  const hasAuthCallback = Boolean(authCode) && !isMockAuth;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">AlphaLens</h1>
      <div className="flex items-center gap-3">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
        <p className="text-gray-600">
          {hasAuthCallback ? "Completing sign in..." : "Loading..."}
        </p>
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen flex-col items-center justify-center p-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">AlphaLens</h1>
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
            <p className="text-gray-600">Loading...</p>
          </div>
        </main>
      }
    >
      <HomeContent />
    </Suspense>
  );
}
