"""In-memory repository for recommendation results."""

from domain.recommendation import RecommendationResult, RecommendationSummary


class RecommendationRepository:
    """In-memory storage for recommendation results.

    Note: This is a simple in-memory implementation for MVP.
    Production should use DynamoDB or similar persistent storage.
    """

    def __init__(self) -> None:
        self._storage: dict[str, RecommendationResult] = {}

    def save(self, result: RecommendationResult) -> str:
        """Save a recommendation result.

        Args:
            result: The result to save

        Returns:
            The run_id of the saved result
        """
        self._storage[result.run_id] = result
        return result.run_id

    def get_by_id(self, run_id: str) -> RecommendationResult | None:
        """Get a recommendation result by ID.

        Args:
            run_id: The unique run identifier

        Returns:
            The result if found, None otherwise
        """
        return self._storage.get(run_id)

    def get_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RecommendationSummary]:
        """Get recommendation summaries for a user.

        Args:
            user_id: The user's ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of RecommendationSummary objects
        """
        # Filter by user
        user_results = [r for r in self._storage.values() if r.user_id == user_id]

        # Sort by created_at (newest first)
        user_results.sort(key=lambda r: r.created_at, reverse=True)

        # Apply pagination
        paginated = user_results[offset : offset + limit]

        # Convert to summaries
        summaries = []
        for result in paginated:
            top_score = result.scores[0] if result.scores else None
            summaries.append(
                RecommendationSummary(
                    run_id=result.run_id,
                    tickers=result.tickers,
                    horizon=result.horizon,
                    top_pick=top_score.ticker if top_score else None,
                    top_score=top_score.composite_score if top_score else None,
                    created_at=result.created_at,
                )
            )

        return summaries

    def delete(self, run_id: str) -> bool:
        """Delete a recommendation result.

        Args:
            run_id: The unique run identifier

        Returns:
            True if deleted, False if not found
        """
        if run_id in self._storage:
            del self._storage[run_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all stored results (for testing)."""
        self._storage.clear()


# Singleton instance for the application
_repository: RecommendationRepository | None = None


def get_recommendation_repository() -> RecommendationRepository:
    """Get the singleton repository instance."""
    global _repository
    if _repository is None:
        _repository = RecommendationRepository()
    return _repository
