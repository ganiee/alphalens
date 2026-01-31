"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * Registration is handled by Cognito Hosted UI.
 * This page redirects to /login where users can sign up via Hosted UI.
 */
export default function RegisterPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/login");
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
    </div>
  );
}
