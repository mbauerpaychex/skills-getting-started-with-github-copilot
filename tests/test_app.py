import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

# Capture initial state once at import time so every test starts from the same baseline
INITIAL_ACTIVITIES = copy.deepcopy(app_module.activities)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state before each test."""
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_all_activities(self):
        response = client.get("/activities")
        data = response.json()
        assert len(data) == len(INITIAL_ACTIVITIES)

    def test_known_activity_is_present(self):
        response = client.get("/activities")
        assert "Chess Club" in response.json()

    def test_activity_has_expected_fields(self):
        chess = client.get("/activities").json()["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup_returns_200(self):
        response = client.post(
            "/activities/Chess Club/signup?email=new@mergington.edu"
        )
        assert response.status_code == 200

    def test_successful_signup_returns_message(self):
        response = client.post(
            "/activities/Chess Club/signup?email=new@mergington.edu"
        )
        assert "new@mergington.edu" in response.json()["message"]

    def test_participant_is_added_to_activity(self):
        client.post("/activities/Chess Club/signup?email=new@mergington.edu")
        participants = client.get("/activities").json()["Chess Club"]["participants"]
        assert "new@mergington.edu" in participants

    def test_duplicate_signup_returns_400(self):
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400

    def test_duplicate_signup_returns_detail(self):
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.json()["detail"] == "Student already signed up"

    def test_unknown_activity_returns_404(self):
        response = client.post(
            "/activities/Unknown Activity/signup?email=new@mergington.edu"
        )
        assert response.status_code == 404

    def test_unknown_activity_returns_detail(self):
        response = client.post(
            "/activities/Unknown Activity/signup?email=new@mergington.edu"
        )
        assert response.json()["detail"] == "Activity not found"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/participants
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister_returns_200(self):
        response = client.delete(
            "/activities/Chess Club/participants?email=michael@mergington.edu"
        )
        assert response.status_code == 200

    def test_successful_unregister_returns_message(self):
        response = client.delete(
            "/activities/Chess Club/participants?email=michael@mergington.edu"
        )
        assert "michael@mergington.edu" in response.json()["message"]

    def test_participant_is_removed_from_activity(self):
        client.delete(
            "/activities/Chess Club/participants?email=michael@mergington.edu"
        )
        participants = client.get("/activities").json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants

    def test_unregister_non_participant_returns_404(self):
        response = client.delete(
            "/activities/Chess Club/participants?email=nothere@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_non_participant_returns_detail(self):
        response = client.delete(
            "/activities/Chess Club/participants?email=nothere@mergington.edu"
        )
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_unknown_activity_returns_404(self):
        response = client.delete(
            "/activities/Unknown Activity/participants?email=michael@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_unknown_activity_returns_detail(self):
        response = client.delete(
            "/activities/Unknown Activity/participants?email=michael@mergington.edu"
        )
        assert response.json()["detail"] == "Activity not found"
