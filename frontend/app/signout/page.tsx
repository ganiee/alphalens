"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/lib/auth-context";

export default function SignOutPage() {
  const { logout, isAuthenticated } = useAuth();
  const router = useRouter();
  const [isSigningOut, setIsSigningOut] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const performLogout = async () => {
      try {
        await logout();
        // Small delay to show the message
        setTimeout(() => {
          router.replace("/login");
        }, 1000);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Sign out failed");
        setIsSigningOut(false);
      }
    };

    if (isAuthenticated) {
      performLogout();
    } else {
      // Already signed out, redirect to login
      router.replace("/login");
    }
  }, [logout, isAuthenticated, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="w-full max-w-md space-y-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900">AlphaLens</h1>

        {error ? (
          <div className="space-y-4">
            <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
            <button
              onClick={() => router.push("/login")}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              Go to Login
            </button>
          </div>
        ) : isSigningOut ? (
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
            </div>
            <p className="text-gray-600">Signing you out...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-gray-600">You have been signed out.</p>
            <button
              onClick={() => router.push("/login")}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              Sign In Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
