"""Provider response caching layer.

Provides caching for external data provider responses to reduce API calls
and improve response times.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class CacheEntry(BaseModel):
    """A cached provider response entry."""

    cache_key: str
    provider: str
    data: dict[str, Any]
    ticker: str
    fetched_at: datetime
    expires_at: datetime


class ProviderCache(ABC):
    """Protocol for provider response caching."""

    @abstractmethod
    def get(self, cache_key: str) -> CacheEntry | None:
        """Get a cached entry by key. Returns None if not found or expired."""
        ...

    @abstractmethod
    def set(self, entry: CacheEntry) -> None:
        """Store a cache entry."""
        ...

    @abstractmethod
    def delete(self, cache_key: str) -> None:
        """Delete a cache entry."""
        ...

    @abstractmethod
    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count of deleted entries."""
        ...


class NoOpCache(ProviderCache):
    """Cache implementation that does nothing (for disabled caching)."""

    def get(self, cache_key: str) -> CacheEntry | None:
        return None

    def set(self, entry: CacheEntry) -> None:
        pass

    def delete(self, cache_key: str) -> None:
        pass

    def clear_expired(self) -> int:
        return 0


class SqliteProviderCache(ProviderCache):
    """SQLite-backed provider cache implementation."""

    def __init__(self, db_path: str, cache_dir: str | None = None):
        """Initialize the SQLite cache.

        Args:
            db_path: Path to the SQLite database file
            cache_dir: Optional directory to create for the cache
        """
        self.db_path = db_path

        # Ensure cache directory exists
        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    data TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider_ticker ON cache_entries(provider, ticker)
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get(self, cache_key: str) -> CacheEntry | None:
        """Get a cached entry by key. Returns None if not found or expired."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT cache_key, provider, data, ticker, fetched_at, expires_at
                FROM cache_entries
                WHERE cache_key = ?
                """,
                (cache_key,),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            expires_at = datetime.fromisoformat(row["expires_at"])
            now = datetime.now(UTC)

            # Check if expired
            if expires_at <= now:
                self.delete(cache_key)
                return None

            return CacheEntry(
                cache_key=row["cache_key"],
                provider=row["provider"],
                data=json.loads(row["data"]),
                ticker=row["ticker"],
                fetched_at=datetime.fromisoformat(row["fetched_at"]),
                expires_at=expires_at,
            )

    def set(self, entry: CacheEntry) -> None:
        """Store a cache entry."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries
                (cache_key, provider, data, ticker, fetched_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.cache_key,
                    entry.provider,
                    json.dumps(entry.data),
                    entry.ticker,
                    entry.fetched_at.isoformat(),
                    entry.expires_at.isoformat(),
                ),
            )
            conn.commit()

    def delete(self, cache_key: str) -> None:
        """Delete a cache entry."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM cache_entries WHERE cache_key = ?", (cache_key,))
            conn.commit()

    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count of deleted entries."""
        now = datetime.now(UTC).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM cache_entries WHERE expires_at <= ?", (now,))
            conn.commit()
            return cursor.rowcount


def make_cache_key(provider: str, operation: str, ticker: str, **params: Any) -> str:
    """Create a standardized cache key.

    Format: {provider}:{operation}:{ticker}:{param1}={value1}:{param2}={value2}...

    Args:
        provider: Provider name (e.g., "polygon", "fmp", "newsapi")
        operation: Operation type (e.g., "price_history", "fundamentals", "news")
        ticker: Stock ticker symbol
        **params: Additional parameters to include in the key

    Returns:
        A formatted cache key string
    """
    key_parts = [provider, operation, ticker]
    for param_name, param_value in sorted(params.items()):
        key_parts.append(f"{param_name}={param_value}")
    return ":".join(key_parts)
