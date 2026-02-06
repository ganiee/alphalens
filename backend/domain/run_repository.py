"""Run repository interface for recommendation storage."""

from typing import Protocol, runtime_checkable

from domain.recommendation import RecommendationResult, RecommendationSummary


@runtime_checkable
class RunRepository(Protocol):
    """Interface for run storage implementations.

    This protocol defines the contract for storing and retrieving
    recommendation results. Implementations can use in-memory storage,
    SQLite, DynamoDB, or other backends.

    The interface is designed to:
    - Support user-scoped access (all operations filter by user_id)
    - Enable pagination for history queries
    - Allow future database implementations without code changes
    """

    def save(self, result: RecommendationResult) -> str:
        """Save a recommendation result.

        Args:
            result: The recommendation result to save

        Returns:
            The run_id of the saved result
        """
        ...

    def get_by_id(self, run_id: str) -> RecommendationResult | None:
        """Get a recommendation result by ID.

        Args:
            run_id: The unique run identifier

        Returns:
            The result if found, None otherwise
        """
        ...

    def get_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RecommendationSummary]:
        """Get recommendation summaries for a user.

        Args:
            user_id: The user's ID (Cognito sub)
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination

        Returns:
            List of RecommendationSummary objects, newest first
        """
        ...

    def delete(self, run_id: str) -> bool:
        """Delete a recommendation result.

        Args:
            run_id: The unique run identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    def clear(self) -> None:
        """Clear all stored results.

        Note: This is primarily for testing purposes.
        Production implementations may choose to raise NotImplementedError.
        """
        ...
