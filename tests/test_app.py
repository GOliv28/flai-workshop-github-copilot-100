"""
Tests for the Mergington High School Activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities state before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict(self, client):
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_contains_expected_activities(self, client):
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_has_required_fields(self, client):
        response = client.get("/activities")
        chess = response.json()["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "new_student@mergington.edu"},
        )
        assert response.status_code == 200
        assert "new_student@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "new_student@mergington.edu"},
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "new_student@mergington.edu" in participants

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Unknown Activity/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_signup_duplicate_returns_400(self, client):
        email = "michael@mergington.edu"  # already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        assert response.status_code == 400

    def test_signup_duplicate_error_message(self, client):
        email = "michael@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        assert "already" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self, client):
        email = "michael@mergington.edu"  # already in Chess Club
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        email = "michael@mergington.edu"
        client.delete(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email not in participants

    def test_unregister_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Unknown Activity/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_unregister_not_enrolled_returns_404(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "not_enrolled@mergington.edu"},
        )
        assert response.status_code == 404

    def test_unregister_not_enrolled_error_message(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "not_enrolled@mergington.edu"},
        )
        assert "not signed up" in response.json()["detail"].lower()
