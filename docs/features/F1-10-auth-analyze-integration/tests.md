# F1-10: Tests

## Test Coverage

### Backend Tests

#### Auth Middleware Tests (`test_auth.py`)
| Test | Status | Description |
|------|--------|-------------|
| `test_me_without_token_returns_401` | Pass | Missing auth header |
| `test_me_with_invalid_token_returns_401` | Pass | Invalid token |
| `test_me_with_valid_user_token` | Pass | Valid user auth |
| `test_me_with_valid_admin_token` | Pass | Admin role extraction |
| `test_me_with_valid_pro_token` | Pass | Pro plan extraction |

#### Recommendations API Tests (`test_recommendations_api.py`)
| Test | Status | Description |
|------|--------|-------------|
| `test_analyze_requires_auth` | Pass | 401 without token |
| `test_analyze_with_valid_token` | Pass | Success with auth |
| `test_get_result_requires_auth` | Pass | 401 without token |
| `test_get_result_not_found` | Pass | 404 for missing result |
| `test_get_result_success` | Pass | Can retrieve own result |
| `test_get_result_wrong_user` | Pass | 403 for other user's result |
| `test_history_requires_auth` | Pass | 401 without token |
| `test_history_empty_new_user` | Pass | Empty list for new user |
| `test_history_lists_runs` | Pass | Lists user's runs |
| `test_history_excludes_other_users` | Pass | Filters by user_id |

### Repository Tests (To Add)

#### RunRepository Protocol Tests
| Test | Status | Description |
|------|--------|-------------|
| `test_in_memory_implements_protocol` | Pending | Type check |
| `test_save_returns_run_id` | Pending | Basic save |
| `test_get_by_id_returns_result` | Pending | Retrieval |
| `test_get_by_user_filters` | Pending | User filtering |
| `test_delete_removes_result` | Pending | Deletion |

## Running Tests

```bash
cd backend
AUTH_MODE=mock pytest -v tests/test_auth.py tests/test_recommendations_api.py
```

## Test Dependencies

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `fastapi.testclient` - API testing
- Mock auth verifier (AUTH_MODE=mock)
