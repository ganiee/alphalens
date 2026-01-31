/**
 * AWS Amplify configuration for Cognito authentication.
 *
 * Environment variables must be set in .env.local:
 * - NEXT_PUBLIC_AWS_REGION
 * - NEXT_PUBLIC_COGNITO_USER_POOL_ID
 * - NEXT_PUBLIC_COGNITO_CLIENT_ID
 * - NEXT_PUBLIC_COGNITO_DOMAIN
 */

import { ResourcesConfig } from "aws-amplify";

const awsRegion = process.env.NEXT_PUBLIC_AWS_REGION || "us-east-1";
const userPoolId = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || "";
const userPoolClientId = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || "";
const cognitoDomain = process.env.NEXT_PUBLIC_COGNITO_DOMAIN || "";

// Determine the redirect URL based on environment
const redirectUrl =
  typeof window !== "undefined"
    ? window.location.origin + "/"
    : "http://localhost:3000/";

export const amplifyConfig: ResourcesConfig = {
  Auth: {
    Cognito: {
      userPoolId,
      userPoolClientId,
      loginWith: {
        oauth: {
          domain: cognitoDomain,
          scopes: ["email", "openid", "profile"],
          redirectSignIn: [redirectUrl],
          redirectSignOut: [redirectUrl],
          responseType: "code",
        },
        email: true,
      },
      signUpVerificationMethod: "code",
      userAttributes: {
        email: {
          required: true,
        },
      },
      passwordFormat: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialCharacters: true,
      },
    },
  },
};

export const isConfigured = (): boolean => {
  return Boolean(userPoolId && userPoolClientId);
};
