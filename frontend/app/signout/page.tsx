"use client";

import { signOut } from "aws-amplify/auth";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

/**
 * Sign-out page that clears all auth state and redirects to login.
 * Access via: /signout
 */
export default function SignOutPage() {
  const router = useRouter();
  const [status, setStatus] = useState("Signing out...");

  useEffect(() => {
    const performSignOut = async () => {
      try {
        // Clear session storage
        if (typeof window !== "undefined") {
          sessionStorage.clear();
          localStorage.clear();
        }

        // Sign out from Cognito
        await signOut({ global: true });

        setStatus("Signed out successfully. Redirecting...");
      } catch (error) {
        console.error("Sign out error:", error);
        setStatus("Clearing session...");

        // Force clear even if signOut fails
        if (typeof window !== "undefined") {
          sessionStorage.clear();
          localStorage.clear();
        }
      } finally {
        // Always redirect to login after a short delay
        setTimeout(() => {
          router.replace("/login");
        }, 1000);
      }
    };

    performSignOut();
  }, [router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
      <p className="mt-4 text-gray-600">{status}</p>
    </div>
  );
}
