"""Recommendation API endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from domain.recommendation import (
    Horizon,
    PlanConstraintError,
    RecommendationRequest,
    RecommendationResult,
    RecommendationSummary,
)
from routers.deps import (
    CurrentUser,
    RecommendationRepoDep,
    RecommendationServiceDep,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class AnalyzeRequest(BaseModel):
    """Request body for analyze endpoint."""

    tickers: list[str]
    horizon: Horizon = Horizon.ONE_MONTH


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint."""

    run_id: str
    result: RecommendationResult


class HistoryResponse(BaseModel):
    """Response from history endpoint."""

    runs: list[RecommendationSummary]
    total: int


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_stocks(
    request: AnalyzeRequest,
    user: CurrentUser,
    service: RecommendationServiceDep,
    repo: RecommendationRepoDep,
) -> AnalyzeResponse:
    """Run stock analysis and get recommendations.

    Args:
        request: Analysis request with tickers and horizon
        user: Current authenticated user
        service: Recommendation service
        repo: Repository for storing results

    Returns:
        AnalyzeResponse with run_id and full result

    Raises:
        400: Invalid request or plan constraint violation
        401: Not authenticated
    """
    try:
        # Create domain request
        domain_request = RecommendationRequest(
            tickers=request.tickers,
            horizon=request.horizon,
        )

        # Run the recommendation pipeline
        result = await service.run(domain_request, user)

        # Store the result
        repo.save(result)

        return AnalyzeResponse(run_id=result.run_id, result=result)

    except PlanConstraintError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message),
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{run_id}", response_model=RecommendationResult)
async def get_result(
    run_id: str,
    user: CurrentUser,
    repo: RecommendationRepoDep,
) -> RecommendationResult:
    """Get a specific recommendation result.

    Args:
        run_id: The unique run identifier
        user: Current authenticated user
        repo: Repository for retrieving results

    Returns:
        The full RecommendationResult

    Raises:
        404: Run not found
        403: Run belongs to different user
        401: Not authenticated
    """
    result = repo.get_by_id(run_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation run '{run_id}' not found",
        )

    # Check ownership
    if result.user_id != user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this recommendation run",
        )

    return result


@router.get("/", response_model=HistoryResponse)
async def get_history(
    user: CurrentUser,
    repo: RecommendationRepoDep,
    limit: int = 50,
    offset: int = 0,
) -> HistoryResponse:
    """Get user's recommendation history.

    Args:
        user: Current authenticated user
        repo: Repository for retrieving results
        limit: Maximum number of results (default 50)
        offset: Number of results to skip (default 0)

    Returns:
        HistoryResponse with list of run summaries

    Raises:
        401: Not authenticated
    """
    runs = repo.get_by_user(user.sub, limit=limit, offset=offset)

    return HistoryResponse(runs=runs, total=len(runs))
