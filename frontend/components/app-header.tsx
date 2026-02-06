"use client";

import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth-context";

interface AppHeaderProps {
  showBackToDashboard?: boolean;
}

export function AppHeader({ showBackToDashboard = true }: AppHeaderProps) {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const plan =
    typeof window !== "undefined"
      ? sessionStorage.getItem("selectedPlan") || "free"
      : "free";

  return (
    <header className="bg-white shadow">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
        <div className="flex items-center gap-4">
          <h1
            className="cursor-pointer text-xl font-bold text-gray-900"
            onClick={() => router.push("/dashboard")}
          >
            AlphaLens
          </h1>
          {user && (
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                plan === "pro"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {plan === "pro" ? "Pro" : "Free"}
            </span>
          )}
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <span className="hidden text-sm text-gray-600 sm:inline">
              {user.email}
            </span>
          )}
          {showBackToDashboard && (
            <button
              onClick={() => router.push("/dashboard")}
              className="rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-700 hover:bg-gray-200"
            >
              Dashboard
            </button>
          )}
          <button
            onClick={handleLogout}
            className="rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-700 hover:bg-gray-200"
          >
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
}
