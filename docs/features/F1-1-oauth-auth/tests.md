# F1-1: OAuth Authentication & Roles - Tests

## Test File Location

`backend/tests/test_auth.py`

## Test Coverage

### Unit Tests

#### TokenPayload Entity
| Test | Description |
|------|-------------|
| `test_to_user_basic` | Basic user conversion sets default role (user) and plan (free) |
| `test_to_user_with_admin_group` | Admin Cognito group adds admin role |
| `test_to_user_with_pro_group` | Pro Cognito group sets pro plan |
| `test_to_user_with_multiple_groups` | Multiple groups processed correctly |

#### MockAuthVerifier
| Test | Description |
|------|-------------|
| `test_valid_user_token` | Valid user token returns correct payload |
| `test_valid_admin_token` | Admin token includes admin group |
| `test_valid_pro_token` | Pro token includes pro group |
| `test_expired_token_raises` | Expired token raises AuthenticationError |
| `test_invalid_token_raises` | Invalid token raises AuthenticationError |
| `test_unknown_token_raises` | Unknown token raises AuthenticationError |

### Integration Tests (API Endpoints)

| Test | Endpoint | Description |
|------|----------|-------------|
| `test_me_without_token_returns_401` | GET /auth/me | Missing auth header returns 401 |
| `test_me_with_invalid_token_returns_401` | GET /auth/me | Invalid token returns 401 |
| `test_me_with_valid_user_token` | GET /auth/me | Valid user token returns user info |
| `test_me_with_valid_admin_token` | GET /auth/me | Admin token shows admin role |
| `test_me_with_valid_pro_token` | GET /auth/me | Pro token shows pro plan |
| `test_admin_check_without_admin_role_returns_403` | GET /auth/admin/check | Non-admin gets 403 |
| `test_admin_check_with_admin_role` | GET /auth/admin/check | Admin can access |
| `test_health_endpoint_still_public` | GET /health | Health check accessible without auth |

## Running Tests

```bash
cd backend
pip install -e .[dev]
pytest tests/test_auth.py -v
```

## Test Strategy

- **Mock Adapter**: All tests use `MockAuthVerifier` (no AWS required)
- **Deterministic**: Fixed test tokens with predictable behavior
- **No External Dependencies**: No network calls or live services
- **Fast Execution**: All tests run in-memory
