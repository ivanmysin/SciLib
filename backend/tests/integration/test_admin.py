"""Tests for admin endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_admin_status(client: TestClient):
    """Test admin status endpoint returns all health checks."""
    response = client.get("/api/v1/admin/status")
    assert response.status_code == 200
    data = response.json()
    assert "database_connected" in data
    assert "redis_connected" in data
    assert "grobid_connected" in data
    assert "worker_running" in data
    assert data["version"] is not None


def test_admin_stats_users(client: TestClient):
    """Test user stats endpoint."""
    response = client.get("/api/v1/admin/stats/users")
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "active_users" in data
    assert "blocked_users" in data
    assert isinstance(data["total_users"], int)
    assert isinstance(data["active_users"], int)
    assert isinstance(data["blocked_users"], int)


def test_admin_stats_storage(client: TestClient):
    """Test storage stats endpoint."""
    response = client.get("/api/v1/admin/stats/storage")
    assert response.status_code == 200
    data = response.json()
    assert "total_bytes" in data
    assert "used_bytes" in data
    assert "file_count" in data
    assert isinstance(data["total_bytes"], int)
    assert isinstance(data["used_bytes"], int)
    assert isinstance(data["file_count"], int)


def test_admin_list_users(client: TestClient):
    """Test list users endpoint."""
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_admin_settings_get(client: TestClient):
    """Test get settings endpoint."""
    response = client.get("/api/v1/admin/settings")
    assert response.status_code == 200
    data = response.json()
    assert "maintenance_mode" in data or len(data) > 0


def test_admin_reset_dry_run(client: TestClient):
    """Test reset endpoint with dry_run=true."""
    response = client.post("/api/v1/admin/reset?dry_run=true")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "would_delete" in data
    assert data["message"] == "Dry run - no changes made"
