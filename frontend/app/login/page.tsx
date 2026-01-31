"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { useAuth, isMockAuth } from "@/lib/auth-context";

type Plan = "free" | "pro" | null;

function LoginContent() {
  const { signInWithHostedUI, isAuthenticated, isLoading, mockLogin } =
    useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [selectedPlan, setSelectedPlan] = useState<Plan>(null);
  const [error, setError] = useState("");
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [mockEmail, setMockEmail] = useState("test@example.com");

  // Check for error from callback
  useEffect(() => {
    const errorParam = searchParams.get("error");
    const errorDescription = searchParams.get("error_description");
    if (errorParam) {
      setError(errorDescription || errorParam);
    }
  }, [searchParams]);

  // Redirect if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  const handleContinue = async () => {
    if (!selectedPlan) return;

    setError("");
    setIsRedirecting(true);

    try {
      // Mock auth mode - login directly
      if (isMockAuth && mockLogin) {
        mockLogin(mockEmail, selectedPlan);
        router.replace("/dashboard");
        return;
      }

      // Real Cognito auth - store plan and redirect
      sessionStorage.setItem("selectedPlan", selectedPlan);
      await signInWithHostedUI();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
      setIsRedirecting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-8">
      <div className="w-full max-w-lg space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">AlphaLens</h1>
          <p className="mt-2 text-gray-600">
            AI-powered stock analysis and insights
          </p>
          {isMockAuth && (
            <p className="mt-2 rounded bg-yellow-100 px-2 py-1 text-sm text-yellow-800">
              Mock Auth Mode (local testing)
            </p>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Mock Auth Email Input */}
        {isMockAuth && (
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              Test Email
            </label>
            <input
              type="email"
              id="email"
              value={mockEmail}
              onChange={(e) => setMockEmail(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="test@example.com"
            />
          </div>
        )}

        {/* Plan Selection */}
        <div className="space-y-4">
          <h2 className="text-center text-lg font-medium text-gray-900">
            Choose your plan
          </h2>

          <div className="grid gap-4 sm:grid-cols-2">
            {/* Free Plan Card */}
            <button
              type="button"
              onClick={() => setSelectedPlan("free")}
              className={`rounded-lg border-2 p-6 text-left transition-all ${
                selectedPlan === "free"
                  ? "border-blue-600 bg-blue-50 ring-2 ring-blue-600"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <div className="mb-4">
                <span className="inline-block rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800">
                  Free
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">
                Basic Access
              </h3>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                $0
                <span className="text-sm font-normal text-gray-500">/month</span>
              </p>
              <ul className="mt-4 space-y-2 text-sm text-gray-600">
                <li className="flex items-center">
                  <CheckIcon />
                  <span className="ml-2">5 analyses per month</span>
                </li>
                <li className="flex items-center">
                  <CheckIcon />
                  <span className="ml-2">Basic indicators</span>
                </li>
                <li className="flex items-center">
                  <CheckIcon />
                  <span className="ml-2">7-day history</span>
                </li>
              </ul>
            </button>

            {/* Pro Plan Card */}
            <button
              type="button"
              onClick={() => setSelectedPlan("pro")}
              className={`rounded-lg border-2 p-6 text-left transition-all ${
                selectedPlan === "pro"
                  ? "border-blue-600 bg-blue-50 ring-2 ring-blue-600"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <div className="mb-4">
                <span className="inline-block rounded-full bg-blue-600 px-3 py-1 text-xs font-medium text-white">
                  Pro
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">
                Full Access
              </h3>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                $19
                <span className="text-sm font-normal text-gray-500">/month</span>
              </p>
              <ul className="mt-4 space-y-2 text-sm text-gray-600">
                <li className="flex items-center">
                  <CheckIcon />
                  <span className="ml-2">Unlimited analyses</span>
                </li>
                <li className="flex items-center">
                  <CheckIcon />
                  <span className="ml-2">Advanced indicators</span>
                </li>
                <li className="flex items-center">
                  <CheckIcon />
                  <span className="ml-2">Full history access</span>
                </li>
                <li className="flex items-center">
                  <CheckIcon />
                  <span className="ml-2">Priority support</span>
                </li>
              </ul>
            </button>
          </div>
        </div>

        {/* Continue Button */}
        <button
          onClick={handleContinue}
          disabled={!selectedPlan || isRedirecting}
          className={`w-full rounded-md px-4 py-3 text-center font-medium transition-all ${
            selectedPlan && !isRedirecting
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "cursor-not-allowed bg-gray-200 text-gray-400"
          }`}
        >
          {isRedirecting ? (
            <span className="flex items-center justify-center">
              <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              {isMockAuth ? "Signing in..." : "Redirecting..."}
            </span>
          ) : (
            "Continue"
          )}
        </button>

        {!selectedPlan && (
          <p className="text-center text-sm text-gray-500">
            Please select a plan to continue
          </p>
        )}

        {/* Disclaimer */}
        <p className="text-center text-xs text-gray-500">
          By continuing, you agree that AlphaLens is for educational purposes
          only and does not constitute financial advice.
        </p>
      </div>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg
      className="h-4 w-4 text-green-500"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
