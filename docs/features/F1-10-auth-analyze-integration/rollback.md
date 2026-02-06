# F1-10: Rollback Plan

## Overview

F1-10 formalizes the auth-analyze integration that was largely implemented in F1-1 and F1-2. Rolling back requires careful consideration of dependencies.

## Rollback Scope

### What Can Be Rolled Back

1. **RunRepository Protocol** (`domain/run_repository.py`)
   - Safe to remove, revert to concrete class usage

2. **Repository Refactoring** (if done)
   - Revert file moves
   - Restore original `repo/recommendations.py`

### What CANNOT Be Rolled Back

The core auth-analyze integration is part of F1-1 and F1-2:
- Token verification middleware
- Protected endpoint decorators
- Frontend auth header integration
- ProtectedRoute component

Rolling back these would break F1-1 and F1-2.

## Rollback Steps

### Step 1: Revert RunRepository Protocol

If the Protocol was added:

```bash
git revert <commit-hash-for-protocol>
```

Or manually:
1. Delete `backend/domain/run_repository.py`
2. Update imports in `deps.py` to use concrete class

### Step 2: Restore Original Repository

If repository was refactored:

```bash
git checkout <pre-f1-10-commit> -- backend/repo/recommendations.py
```

### Step 3: Update Feature Index

```markdown
| F1-10 | 1 | Rolled Back | Auth-Analyze Integration | ... |
```

## Verification After Rollback

```bash
cd backend
AUTH_MODE=mock pytest -v
```

All tests should still pass as the core functionality remains.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking F1-1/F1-2 | Low | High | Only roll back F1-10-specific changes |
| Test failures | Low | Medium | Verify tests before completing rollback |
| Import errors | Medium | Low | Check all imports after file changes |

## Decision Matrix

| Scenario | Recommendation |
|----------|----------------|
| Protocol causes type errors | Roll back Protocol only |
| Repository refactor breaks tests | Roll back refactor only |
| Core auth flow broken | Do NOT roll back - fix forward |
