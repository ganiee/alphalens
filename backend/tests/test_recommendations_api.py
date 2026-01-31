"""Tests for the recommendations API endpoints."""

import pytest
from fastapi.testclient import TestClient

from main import app
from repo.recommendations import get_recommendation_repository

client = TestClient(app)


# Test tokens from mock auth adapter
USER_TOKEN = "test-user-token"
ADMIN_TOKEN = "test-admin-token"
PRO_TOKEN = "test-pro-token"


@pytest.fixture(autouse=True)
def clear_repository():
    """Clear the repository before each test."""
    repo = get_recommendation_repository()
    repo.clear()
    yield
    repo.clear()


class TestAnalyzeEndpoint:
    """Tests for POST /recommendations/analyze."""

    def test_analyze_requires_auth(self):
        """Test analyze endpoint requires authentication."""
        response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL"], "horizon": "1M"},
        )
        assert response.status_code == 401

    def test_analyze_with_valid_token(self):
        """Test analyze returns result with valid auth."""
        response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL", "MSFT"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "run_id" in data
        assert "result" in data
        assert len(data["result"]["scores"]) == 2

    def test_analyze_invalid_ticker(self):
        """Test analyze rejects invalid ticker format."""
        response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["INVALID123"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 400

    def test_analyze_empty_tickers(self):
        """Test analyze rejects empty ticker list."""
        response = client.post(
            "/recommendations/analyze",
            json={"tickers": [], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code in [400, 422]  # Validation error

    def test_analyze_too_many_tickers_free(self):
        """Test free user cannot analyze more than 3 tickers."""
        response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 400
        assert "3" in response.json()["detail"]

    def test_analyze_max_tickers_pro(self):
        """Test pro user can analyze up to 5 tickers."""
        response = client.post(
            "/recommendations/analyze",
            json={
                "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
                "horizon": "1M",
            },
            headers={"Authorization": f"Bearer {PRO_TOKEN}"},
        )
        assert response.status_code == 200
        assert len(response.json()["result"]["scores"]) == 5

    def test_analyze_invalid_horizon_free(self):
        """Test free user cannot use non-1M horizons."""
        response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL"], "horizon": "3M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 400
        assert "horizon" in response.json()["detail"].lower()

    def test_analyze_valid_horizon_pro(self):
        """Test pro user can use any horizon."""
        for horizon in ["1W", "1M", "3M", "6M", "1Y"]:
            response = client.post(
                "/recommendations/analyze",
                json={"tickers": ["AAPL"], "horizon": horizon},
                headers={"Authorization": f"Bearer {PRO_TOKEN}"},
            )
            assert response.status_code == 200

    def test_analyze_returns_run_id(self):
        """Test analyze returns a unique run_id."""
        response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 200

        run_id = response.json()["run_id"]
        assert run_id is not None
        assert len(run_id) > 0

    def test_analyze_result_structure(self):
        """Test analyze result has correct structure."""
        response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 200

        result = response.json()["result"]
        assert "run_id" in result
        assert "user_id" in result
        assert "tickers" in result
        assert "horizon" in result
        assert "scores" in result
        assert "evidence" in result
        assert "created_at" in result

        # Check score structure
        score = result["scores"][0]
        assert "ticker" in score
        assert "composite_score" in score
        assert "breakdown" in score
        assert "rank" in score
        assert "allocation_pct" in score


class TestGetResultEndpoint:
    """Tests for GET /recommendations/{run_id}."""

    def test_get_result_requires_auth(self):
        """Test get result requires authentication."""
        response = client.get("/recommendations/some-run-id")
        assert response.status_code == 401

    def test_get_result_not_found(self):
        """Test get result returns 404 for non-existent run."""
        response = client.get(
            "/recommendations/non-existent-id",
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 404

    def test_get_result_success(self):
        """Test get result returns the stored result."""
        # First create a result
        create_response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        run_id = create_response.json()["run_id"]

        # Then retrieve it
        get_response = client.get(
            f"/recommendations/{run_id}",
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert get_response.status_code == 200

        result = get_response.json()
        assert result["run_id"] == run_id
        assert result["tickers"] == ["AAPL"]

    def test_get_result_wrong_user(self):
        """Test get result returns 403 for wrong user."""
        # Create result as one user
        create_response = client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        run_id = create_response.json()["run_id"]

        # Try to access as different user (admin is different user)
        get_response = client.get(
            f"/recommendations/{run_id}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
        )
        assert get_response.status_code == 403


class TestHistoryEndpoint:
    """Tests for GET /recommendations/."""

    def test_history_requires_auth(self):
        """Test history requires authentication."""
        response = client.get("/recommendations/")
        assert response.status_code == 401

    def test_history_empty_new_user(self):
        """Test history returns empty list for new user."""
        response = client.get(
            "/recommendations/",
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 200
        assert response.json()["runs"] == []
        assert response.json()["total"] == 0

    def test_history_lists_runs(self):
        """Test history lists user's runs."""
        # Create some runs
        for tickers in [["AAPL"], ["MSFT"], ["GOOGL"]]:
            client.post(
                "/recommendations/analyze",
                json={"tickers": tickers, "horizon": "1M"},
                headers={"Authorization": f"Bearer {USER_TOKEN}"},
            )

        # Get history
        response = client.get(
            "/recommendations/",
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 3
        assert len(data["runs"]) == 3

    def test_history_excludes_other_users(self):
        """Test history only shows user's own runs."""
        # Create run as one user
        client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )

        # Check history as different user
        response = client.get(
            "/recommendations/",
            headers={"Authorization": f"Bearer {PRO_TOKEN}"},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_history_summary_fields(self):
        """Test history returns summary fields."""
        client.post(
            "/recommendations/analyze",
            json={"tickers": ["AAPL", "MSFT"], "horizon": "1M"},
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )

        response = client.get(
            "/recommendations/",
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
        )
        assert response.status_code == 200

        run = response.json()["runs"][0]
        assert "run_id" in run
        assert "tickers" in run
        assert "horizon" in run
        assert "top_pick" in run
        assert "top_score" in run
        assert "created_at" in run
