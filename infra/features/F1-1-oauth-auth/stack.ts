#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as ssm from "aws-cdk-lib/aws-ssm";

/**
 * F1-1: OAuth Authentication & Roles - Cognito Infrastructure
 *
 * Stack Name Convention: alphalens-<env>-F1-1-cognito
 *
 * Creates:
 * - Cognito User Pool with email sign-in
 * - App Client for frontend (public, no secret)
 * - Hosted UI domain
 * - User groups (admin, pro)
 * - SSM Parameters for config hydration
 */

interface F1_1_CognitoStackProps extends cdk.StackProps {
  environment: "dev" | "stage" | "prod";
  domainPrefix?: string;
  callbackUrls?: string[];
  logoutUrls?: string[];
}

export class F1_1_CognitoStack extends cdk.Stack {
  public readonly userPoolId: string;
  public readonly clientId: string;
  public readonly domain: string;

  constructor(scope: cdk.App, id: string, props: F1_1_CognitoStackProps) {
    super(scope, id, props);

    const environment = props.environment;
    const domainPrefix = props.domainPrefix || `alphalens-${environment}`;
    const callbackUrls = props.callbackUrls || [
      "http://localhost:3000/",
      "http://localhost:3001/",
    ];
    const logoutUrls = props.logoutUrls || [
      "http://localhost:3000/",
      "http://localhost:3001/",
    ];

    // Create User Pool
    const userPool = new cognito.UserPool(this, "UserPool", {
      userPoolName: `alphalens-${environment}-users`,
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
      removalPolicy:
        environment === "prod"
          ? cdk.RemovalPolicy.RETAIN
          : cdk.RemovalPolicy.DESTROY,
    });

    // Create Hosted UI Domain
    const domain = userPool.addDomain("Domain", {
      cognitoDomain: {
        domainPrefix: domainPrefix,
      },
    });

    // Create App Client (public client for frontend)
    const userPoolClient = userPool.addClient("WebClient", {
      userPoolClientName: `alphalens-${environment}-web`,
      generateSecret: false,
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

    // Store outputs in class properties
    this.userPoolId = userPool.userPoolId;
    this.clientId = userPoolClient.userPoolClientId;
    this.domain = `${domainPrefix}.auth.${this.region}.amazoncognito.com`;

    // SSM Parameters for config hydration
    new ssm.StringParameter(this, "UserPoolIdParam", {
      parameterName: `/alphalens/${environment}/auth/userPoolId`,
      stringValue: userPool.userPoolId,
      description: "Cognito User Pool ID",
    });

    new ssm.StringParameter(this, "ClientIdParam", {
      parameterName: `/alphalens/${environment}/auth/clientId`,
      stringValue: userPoolClient.userPoolClientId,
      description: "Cognito App Client ID",
    });

    new ssm.StringParameter(this, "DomainParam", {
      parameterName: `/alphalens/${environment}/auth/domain`,
      stringValue: this.domain,
      description: "Cognito Hosted UI Domain",
    });

    new ssm.StringParameter(this, "RegionParam", {
      parameterName: `/alphalens/${environment}/auth/region`,
      stringValue: this.region,
      description: "AWS Region",
    });

    // CloudFormation Outputs
    new cdk.CfnOutput(this, "UserPoolId", {
      value: userPool.userPoolId,
      description: "Cognito User Pool ID",
      exportName: `alphalens-${environment}-F1-1-UserPoolId`,
    });

    new cdk.CfnOutput(this, "UserPoolClientId", {
      value: userPoolClient.userPoolClientId,
      description: "Cognito App Client ID",
      exportName: `alphalens-${environment}-F1-1-ClientId`,
    });

    new cdk.CfnOutput(this, "CognitoDomain", {
      value: this.domain,
      description: "Cognito Hosted UI Domain",
      exportName: `alphalens-${environment}-F1-1-Domain`,
    });

    new cdk.CfnOutput(this, "Region", {
      value: this.region,
      description: "AWS Region",
      exportName: `alphalens-${environment}-F1-1-Region`,
    });

    new cdk.CfnOutput(this, "HostedUIUrl", {
      value: domain.signInUrl(userPoolClient, {
        redirectUri: callbackUrls[0],
      }),
      description: "Cognito Hosted UI Sign-in URL",
    });
  }
}
