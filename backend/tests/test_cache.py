"""Tests for the provider caching layer."""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from adapters.cache import (
    CacheEntry,
    NoOpCache,
    SqliteProviderCache,
    make_cache_key,
)


class TestMakeCacheKey:
    """Tests for cache key generation."""

    def test_basic_key(self):
        """Test basic cache key format."""
        key = make_cache_key("polygon", "price_history", "AAPL")
        assert key == "polygon:price_history:AAPL"

    def test_key_with_params(self):
        """Test cache key with additional parameters."""
        key = make_cache_key("polygon", "price_history", "AAPL", days=200)
        assert key == "polygon:price_history:AAPL:days=200"

    def test_key_with_multiple_params(self):
        """Test cache key with multiple parameters (sorted)."""
        key = make_cache_key("newsapi", "news", "MSFT", max_articles=5, language="en")
        assert key == "newsapi:news:MSFT:language=en:max_articles=5"


class TestNoOpCache:
    """Tests for the NoOpCache implementation."""

    def test_get_returns_none(self):
        """Test get always returns None."""
        cache = NoOpCache()
        result = cache.get("any:key")
        assert result is None

    def test_set_does_nothing(self):
        """Test set completes without error."""
        cache = NoOpCache()
        entry = CacheEntry(
            cache_key="test:key",
            provider="test",
            data={"foo": "bar"},
            ticker="TEST",
            fetched_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        cache.set(entry)  # Should not raise

    def test_delete_does_nothing(self):
        """Test delete completes without error."""
        cache = NoOpCache()
        cache.delete("any:key")  # Should not raise

    def test_clear_expired_returns_zero(self):
        """Test clear_expired returns 0."""
        cache = NoOpCache()
        result = cache.clear_expired()
        assert result == 0


class TestSqliteProviderCache:
    """Tests for the SQLite cache implementation."""

    @pytest.fixture
    def cache(self):
        """Create a temporary SQLite cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.sqlite"
            yield SqliteProviderCache(str(db_path))

    def test_set_and_get(self, cache):
        """Test storing and retrieving a cache entry."""
        now = datetime.now(UTC)
        entry = CacheEntry(
            cache_key="polygon:price_history:AAPL:days=200",
            provider="polygon",
            data={"closes": [100, 101, 102]},
            ticker="AAPL",
            fetched_at=now,
            expires_at=now + timedelta(hours=1),
        )

        cache.set(entry)
        result = cache.get("polygon:price_history:AAPL:days=200")

        assert result is not None
        assert result.cache_key == entry.cache_key
        assert result.provider == "polygon"
        assert result.data == {"closes": [100, 101, 102]}
        assert result.ticker == "AAPL"

    def test_get_miss_returns_none(self, cache):
        """Test get returns None for non-existent key."""
        result = cache.get("nonexistent:key")
        assert result is None

    def test_get_expired_returns_none(self, cache):
        """Test get returns None for expired entries."""
        now = datetime.now(UTC)
        entry = CacheEntry(
            cache_key="polygon:price_history:AAPL:days=200",
            provider="polygon",
            data={"closes": [100]},
            ticker="AAPL",
            fetched_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),  # Already expired
        )

        cache.set(entry)
        result = cache.get("polygon:price_history:AAPL:days=200")

        assert result is None

    def test_delete(self, cache):
        """Test deleting a cache entry."""
        now = datetime.now(UTC)
        entry = CacheEntry(
            cache_key="test:key",
            provider="test",
            data={"foo": "bar"},
            ticker="TEST",
            fetched_at=now,
            expires_at=now + timedelta(hours=1),
        )

        cache.set(entry)
        assert cache.get("test:key") is not None

        cache.delete("test:key")
        assert cache.get("test:key") is None

    def test_clear_expired(self, cache):
        """Test clearing expired entries."""
        now = datetime.now(UTC)

        # Add expired entry
        expired_entry = CacheEntry(
            cache_key="expired:key",
            provider="test",
            data={"status": "old"},
            ticker="OLD",
            fetched_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
        cache.set(expired_entry)

        # Add valid entry
        valid_entry = CacheEntry(
            cache_key="valid:key",
            provider="test",
            data={"status": "new"},
            ticker="NEW",
            fetched_at=now,
            expires_at=now + timedelta(hours=1),
        )
        cache.set(valid_entry)

        # Clear expired
        count = cache.clear_expired()

        # Should have removed 1 entry
        assert count == 1
        assert cache.get("expired:key") is None
        assert cache.get("valid:key") is not None

    def test_overwrite_existing(self, cache):
        """Test that set overwrites existing entries."""
        now = datetime.now(UTC)
        key = "test:overwrite"

        # Set initial value
        entry1 = CacheEntry(
            cache_key=key,
            provider="test",
            data={"value": 1},
            ticker="TEST",
            fetched_at=now,
            expires_at=now + timedelta(hours=1),
        )
        cache.set(entry1)

        # Overwrite with new value
        entry2 = CacheEntry(
            cache_key=key,
            provider="test",
            data={"value": 2},
            ticker="TEST",
            fetched_at=now,
            expires_at=now + timedelta(hours=1),
        )
        cache.set(entry2)

        result = cache.get(key)
        assert result is not None
        assert result.data == {"value": 2}

    def test_creates_cache_directory(self):
        """Test that cache directory is created if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "dir" / "cache.sqlite"
            SqliteProviderCache(str(nested_path))  # Creates directory on init

            assert nested_path.parent.exists()

    def test_complex_data_serialization(self, cache):
        """Test caching complex nested data structures."""
        now = datetime.now(UTC)
        complex_data = {
            "ticker": "AAPL",
            "dates": ["2024-01-01", "2024-01-02"],
            "nested": {"opens": [100.0, 101.5], "closes": [101.0, 102.0]},
            "count": 2,
        }

        entry = CacheEntry(
            cache_key="test:complex",
            provider="test",
            data=complex_data,
            ticker="AAPL",
            fetched_at=now,
            expires_at=now + timedelta(hours=1),
        )

        cache.set(entry)
        result = cache.get("test:complex")

        assert result is not None
        assert result.data == complex_data
