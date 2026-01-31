"""Authentication router for user info endpoints."""

from fastapi import APIRouter

from routers.deps import AdminUser, CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_current_user_info(user: CurrentUser) -> dict:
    """Get current authenticated user information.

    Returns user profile including email, roles, and plan.

    Requires: Valid JWT token in Authorization header
    """
    return {
        "sub": user.sub,
        "email": user.email,
        "email_verified": user.email_verified,
        "roles": [role.value for role in user.roles],
        "plan": user.plan.value,
    }


@router.get("/admin/check")
async def check_admin_access(user: AdminUser) -> dict:
    """Check if current user has admin access.

    This endpoint is only accessible to users with admin role.

    Requires: Valid JWT token with admin role
    """
    return {
        "message": "Admin access confirmed",
        "email": user.email,
    }
