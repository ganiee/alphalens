"""HTTP client with retry support for external API calls."""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class RetryingHttpClient:
    """HTTP client with configurable timeout and retry logic."""

    def __init__(
        self,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.5,
    ):
        """Initialize the retrying HTTP client.

        Args:
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff_seconds: Base delay between retries (exponential backoff)
        """
        self.timeout = httpx.Timeout(timeout_seconds)
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:
        """Make a GET request with retry logic.

        Args:
            url: The URL to request
            params: Query parameters
            headers: Request headers

        Returns:
            The HTTP response

        Raises:
            httpx.HTTPError: If all retries are exhausted
        """
        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"Request timeout (attempt {attempt + 1}/{self.max_retries + 1}): {url}"
                )
            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx), only server errors (5xx)
                if e.response.status_code < 500:
                    raise
                last_error = e
                logger.warning(
                    f"Server error {e.response.status_code} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1}): {url}"
                )
            except httpx.HTTPError as e:
                last_error = e
                logger.warning(
                    f"HTTP error (attempt {attempt + 1}/{self.max_retries + 1}): {url} - {e}"
                )

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                delay = self.retry_backoff_seconds * (2**attempt)
                await asyncio.sleep(delay)

        # All retries exhausted
        if last_error:
            raise last_error
        raise httpx.HTTPError(f"Request failed after {self.max_retries + 1} attempts")

    async def __aenter__(self) -> "RetryingHttpClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
