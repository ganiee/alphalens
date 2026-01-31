#!/usr/bin/env node
/**
 * AlphaLens Infrastructure - Main CDK App
 *
 * This is the entry point for all CDK stacks.
 * Each feature owns its infrastructure module under /infra/features/<FeatureID>/
 *
 * Usage:
 *   make infra-deploy ENV=dev FEATURE=F1-1
 *   make infra-destroy ENV=dev FEATURE=F1-1
 */

import * as cdk from "aws-cdk-lib";
import { F1_1_CognitoStack } from "./features/F1-1-oauth-auth/stack";

// Get environment from context or env var
const app = new cdk.App();

const environment = (app.node.tryGetContext("env") ||
  process.env.INFRA_ENV ||
  "dev") as "dev" | "stage" | "prod";

const feature = app.node.tryGetContext("feature") || process.env.INFRA_FEATURE;

const account =
  process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID || "";
const region =
  process.env.CDK_DEFAULT_REGION || process.env.AWS_REGION || "us-east-2";

// Stack naming convention: alphalens-<env>-<FeatureID>-<purpose>
const stackProps: cdk.StackProps = {
  env: { account, region },
  description: `AlphaLens ${environment} infrastructure`,
};

// Deploy feature-specific stacks based on FEATURE context
if (!feature || feature === "F1-1") {
  new F1_1_CognitoStack(app, `alphalens-${environment}-F1-1-cognito`, {
    ...stackProps,
    environment,
    domainPrefix: environment === "dev" ? "alphalens-auth" : `alphalens-${environment}`,
    callbackUrls:
      environment === "dev"
        ? ["http://localhost:3000/", "http://localhost:3001/"]
        : [`https://alphalens-${environment}.vercel.app/`],
    logoutUrls:
      environment === "dev"
        ? ["http://localhost:3000/", "http://localhost:3001/"]
        : [`https://alphalens-${environment}.vercel.app/`],
  });
}

// Add future feature stacks here:
// if (!feature || feature === "F1-2") {
//   new F1_2_SomeStack(app, `alphalens-${environment}-F1-2-something`, { ... });
// }

app.synth();
