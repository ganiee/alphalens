"use client";

import { Amplify } from "aws-amplify";
import { useEffect, useState, type ReactNode } from "react";

import { amplifyConfig, isConfigured } from "@/lib/amplify-config";
import { AuthProvider } from "@/lib/auth-context";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const [isAmplifyConfigured, setIsAmplifyConfigured] = useState(false);

  useEffect(() => {
    if (isConfigured()) {
      console.log("Amplify config:", JSON.stringify(amplifyConfig, null, 2));
      Amplify.configure(amplifyConfig, { ssr: true });
      setIsAmplifyConfigured(true);
      console.log("Amplify configured successfully");
    } else {
      // Allow app to run without Cognito for development
      console.warn(
        "Cognito not configured. Set NEXT_PUBLIC_COGNITO_* environment variables."
      );
      setIsAmplifyConfigured(true);
    }
  }, []);

  if (!isAmplifyConfigured) {
    return null;
  }

  return <AuthProvider>{children}</AuthProvider>;
}
