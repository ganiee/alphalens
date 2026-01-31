# Infrastructure Index

This file is the single source of truth mapping Feature IDs to their infrastructure modules, stacks, outputs, and consumers.

| Feature ID | Stack Name | Module Path | Purpose | Key Outputs | Consumed By | Deploy Command | Rollback Command |
|------------|------------|-------------|---------|-------------|-------------|----------------|------------------|
| F1-1 | alphalens-dev-F1-1-cognito | /infra/features/F1-1-oauth-auth | Cognito User Pool, App Client, Hosted UI Domain | UserPoolId, ClientId, CognitoDomain, Region | Frontend (login), Backend (JWT verification) | `make infra-deploy ENV=dev FEATURE=F1-1` | `make infra-destroy ENV=dev FEATURE=F1-1` |

## Output Details

### F1-1: OAuth Authentication & Roles

**CloudFormation Outputs:**
- `UserPoolId` - Cognito User Pool ID
- `UserPoolClientId` - App Client ID for frontend
- `CognitoDomain` - Hosted UI domain
- `Region` - AWS region
- `HostedUIUrl` - Full sign-in URL

**SSM Parameters (future):**
- `/alphalens/dev/auth/userPoolId`
- `/alphalens/dev/auth/clientId`
- `/alphalens/dev/auth/domain`

**Current Values (dev):**
- User Pool ID: `us-east-2_1YyHK37iq`
- Client ID: `32tsn6g00gvp02t6kqq67u5s9f`
- Domain: `alphalens-auth.auth.us-east-2.amazoncognito.com`
- Region: `us-east-2`
