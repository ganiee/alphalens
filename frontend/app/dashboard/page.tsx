"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/lib/auth-context";

interface UserInfo {
  sub: string;
  email: string;
  roles: string[];
  plan: string;
  email_verified: boolean;
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}

function DashboardContent() {
  const { user, accessToken } = useAuth();
  const router = useRouter();
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUserInfo = async () => {
      if (!accessToken) {
        setIsLoading(false);
        return;
      }

      // Get selected plan from sessionStorage (set during login)
      const selectedPlan =
        typeof window !== "undefined"
          ? sessionStorage.getItem("selectedPlan") || "free"
          : "free";

      try {
        const backendUrl =
          process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        const response = await fetch(`${backendUrl}/auth/me`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          // Use backend plan if available, otherwise use selected plan
          setUserInfo({
            ...data,
            plan: data.plan || selectedPlan,
          });
        } else {
          // Backend not available - use client-side info
          setUserInfo({
            sub: user?.sub || "",
            email: user?.email || "",
            roles: ["user"],
            plan: selectedPlan,
            email_verified: user?.emailVerified || false,
          });
        }
      } catch {
        // Backend not available - use client-side info
        setUserInfo({
          sub: user?.sub || "",
          email: user?.email || "",
          roles: ["user"],
          plan: selectedPlan,
          email_verified: user?.emailVerified || false,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserInfo();
  }, [accessToken, user]);

  const handleLogout = () => {
    router.push("/signout");
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
      </div>
    );
  }

  const planLabel = userInfo?.plan === "pro" ? "Pro" : "Free";
  const planColor =
    userInfo?.plan === "pro"
      ? "bg-blue-600 text-white"
      : "bg-gray-100 text-gray-800";

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">AlphaLens</h1>
          <button
            onClick={handleLogout}
            className="rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-700 hover:bg-gray-200"
          >
            Sign Out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-600">
            Welcome back, {userInfo?.email || user?.email}
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* User Profile Card */}
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Profile
            </h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-500">Email:</span>
                <span className="ml-2 text-gray-900">
                  {userInfo?.email || user?.email}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Email Verified:</span>
                <span className="ml-2">
                  {userInfo?.email_verified ? (
                    <span className="text-green-600">Yes</span>
                  ) : (
                    <span className="text-yellow-600">No</span>
                  )}
                </span>
              </div>
              <div>
                <span className="text-gray-500">User ID:</span>
                <span className="ml-2 font-mono text-xs text-gray-600">
                  {userInfo?.sub || user?.sub}
                </span>
              </div>
            </div>
          </div>

          {/* Plan Card */}
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">Plan</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-500">Current Plan:</span>
                <span
                  className={`ml-2 rounded-full px-3 py-1 text-xs font-medium ${planColor}`}
                >
                  {planLabel}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Roles:</span>
                <span className="ml-2 text-gray-900">
                  {(userInfo?.roles || ["user"]).join(", ")}
                </span>
              </div>
              {userInfo?.plan === "free" && (
                <p className="mt-2 text-xs text-gray-500">
                  5 analyses per month, basic indicators
                </p>
              )}
              {userInfo?.plan === "pro" && (
                <p className="mt-2 text-xs text-gray-500">
                  Unlimited analyses, advanced indicators
                </p>
              )}
            </div>
          </div>

          {/* Quick Actions Card */}
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Quick Actions
            </h3>
            <div className="space-y-3">
              <button
                disabled
                className="w-full rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-400"
              >
                Run Analysis (Coming Soon)
              </button>
              <button
                disabled
                className="w-full rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-400"
              >
                View History (Coming Soon)
              </button>
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-md bg-yellow-50 p-4 text-sm text-yellow-800">
          <strong>Disclaimer:</strong> AlphaLens is for educational purposes
          only. The information provided does not constitute financial advice.
          Always do your own research before making investment decisions.
        </div>
      </main>
    </div>
  );
}
