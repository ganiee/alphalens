#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import * as cognito from "aws-cdk-lib/aws-cognito";

/**
 * AlphaLens Cognito Infrastructure Stack
 *
 * Creates:
 * - Cognito User Pool with email sign-in
 * - App Client for frontend (public, no secret)
 * - Hosted UI domain
 * - Google OAuth (optional, requires manual config)
 */
class AlphaLensCognitoStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Get configuration from context or use defaults
    const domainPrefix =
      this.node.tryGetContext("domainPrefix") || "alphalens-auth";
    const callbackUrls = this.node.tryGetContext("callbackUrls") || [
      "http://localhost:3000/",
    ];
    const logoutUrls = this.node.tryGetContext("logoutUrls") || [
      "http://localhost:3000/",
    ];

    // Create User Pool
    const userPool = new cognito.UserPool(this, "AlphaLensUserPool", {
      userPoolName: "alphalens-users",
      selfSignUpEnabled: true,
      signInAliases: {
        email: true,
      },
      autoVerify: {
        email: true,
      },
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
      },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev - change for prod
    });

    // Create Hosted UI Domain
    const domain = userPool.addDomain("AlphaLensDomain", {
      cognitoDomain: {
        domainPrefix: domainPrefix,
      },
    });

    // Create App Client (public client for frontend)
    const userPoolClient = userPool.addClient("AlphaLensWebClient", {
      userPoolClientName: "alphalens-web",
      generateSecret: false, // Public client - no secret
      authFlows: {
        userPassword: true,
        userSrp: true,
      },
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
        },
        scopes: [
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.PROFILE,
        ],
        callbackUrls: callbackUrls,
        logoutUrls: logoutUrls,
      },
      preventUserExistenceErrors: true,
    });

    // Create admin group
    new cognito.CfnUserPoolGroup(this, "AdminGroup", {
      userPoolId: userPool.userPoolId,
      groupName: "admin",
      description: "Administrator users",
    });

    // Create pro group (for paid users)
    new cognito.CfnUserPoolGroup(this, "ProGroup", {
      userPoolId: userPool.userPoolId,
      groupName: "pro",
      description: "Pro tier users",
    });

    // Outputs - these are the values needed for the app
    new cdk.CfnOutput(this, "UserPoolId", {
      value: userPool.userPoolId,
      description: "Cognito User Pool ID",
      exportName: "AlphaLensUserPoolId",
    });

    new cdk.CfnOutput(this, "UserPoolClientId", {
      value: userPoolClient.userPoolClientId,
      description: "Cognito App Client ID",
      exportName: "AlphaLensClientId",
    });

    new cdk.CfnOutput(this, "CognitoDomain", {
      value: `${domainPrefix}.auth.${this.region}.amazoncognito.com`,
      description: "Cognito Hosted UI Domain",
      exportName: "AlphaLensCognitoDomain",
    });

    new cdk.CfnOutput(this, "Region", {
      value: this.region,
      description: "AWS Region",
      exportName: "AlphaLensRegion",
    });

    // Output the hosted UI URL for convenience
    new cdk.CfnOutput(this, "HostedUIUrl", {
      value: domain.signInUrl(userPoolClient, {
        redirectUri: callbackUrls[0],
      }),
      description: "Cognito Hosted UI Sign-in URL",
    });
  }
}

// Create the app
const app = new cdk.App();

new AlphaLensCognitoStack(app, "AlphaLensCognitoStack", {
  env: {
    region: process.env.CDK_DEFAULT_REGION || process.env.AWS_REGION || "us-east-1",
    account: process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID,
  },
  description: "AlphaLens Cognito authentication infrastructure",
});

app.synth();
