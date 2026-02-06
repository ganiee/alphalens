# F1-10: Auth-Analyze Integration (End-to-End Flow)

## Overview

This feature connects OAuth authentication to the analyze API flow, ensuring:
1. Only authenticated users can run stock analysis
2. All run outputs are attributed to the authenticated user
3. Users can only access their own analysis results

## Current State (Pre-Implementation)

Most of this feature is already implemented as part of F1-1 and F1-2:
- Token verification middleware exists in `routers/deps.py`
- Protected endpoints require `CurrentUser` dependency
- Frontend sends Bearer token via API client
- `RecommendationRepository` stores results with `user_id`
- Ownership checks prevent cross-user access

## Remaining Work

### 1. Formalize RunRepository Interface

Create a Protocol for the repository to enable future database implementations:

```python
from typing import Protocol

class RunRepository(Protocol):
    def save(self, result: RecommendationResult) -> str: ...
    def get_by_id(self, run_id: str) -> RecommendationResult | None: ...
    def get_by_user(self, user_id: str, limit: int, offset: int) -> list[RecommendationSummary]: ...
    def delete(self, run_id: str) -> bool: ...
```

### 2. Verify End-to-End Flow

Ensure the complete flow works:
1. User signs in via OAuth (Cognito)
2. Frontend stores access token
3. Frontend sends token on analyze request
4. Backend verifies token and extracts user_id
5. Analysis runs and result is stored with user_id
6. User can retrieve their results from history

### 3. Document the Flow

Create architecture documentation showing the auth-analyze integration.

## Architecture

```
Frontend                    Backend
--------                    -------
[Login Page]
    |
    v
[Cognito OAuth] --> [Access Token]
    |
    v
[Auth Context] --> stores token
    |
    v
[Analyze Page] --> POST /recommendations/analyze
    |                     |
    |                     v
    |              [Auth Middleware]
    |                     |
    |              verify JWT, extract user_id
    |                     |
    |                     v
    |              [RecommendationService]
    |                     |
    |              run analysis
    |                     |
    |                     v
    |              [RunRepository]
    |                     |
    |              save with user_id
    |                     |
    v                     v
[Results Page] <-- GET /recommendations/{run_id}
```

## API Contract

### Protected Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/recommendations/analyze` | POST | Required | Run stock analysis |
| `/recommendations/{run_id}` | GET | Required | Get specific result |
| `/recommendations/` | GET | Required | Get user's history |

### Error Responses

| Status | Condition |
|--------|-----------|
| 401 | Missing or invalid token |
| 403 | Accessing another user's result |
| 400 | Invalid request or plan constraint |

## Dependencies

- F1-1: OAuth Authentication (provides auth infrastructure)
- F1-2: Recommendation Engine (provides scoring logic)

## Non-Goals

- Database persistence (interface only)
- Usage limit enforcement (F1-3)
- Token refresh logic (use existing F1-1 implementation)
