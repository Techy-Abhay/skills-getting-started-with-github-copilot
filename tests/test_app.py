from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as activities_store

client = TestClient(app)
initial_activities = deepcopy(activities_store)


@pytest.fixture(autouse=True)
def reset_activities():
    activities_store.clear()
    activities_store.update(deepcopy(initial_activities))
    yield


def _activity_path(activity_name: str, action: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}/{action}"


def test_get_activities_returns_all_activities():
    # Arrange
    expected_activity = "Chess Club"
    expected_other_activity = "Programming Class"
    url = "/activities"

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert expected_activity in payload
    assert expected_other_activity in payload


def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    url = _activity_path(activity_name, "signup")

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities_store[activity_name]["participants"]


def test_signup_for_nonexistent_activity_returns_404():
    # Arrange
    url = _activity_path("Hockey Club", "signup")
    email = "student@mergington.edu"

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_participant_returns_400():
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"
    url = _activity_path(activity_name, "signup")

    # Act
    response = client.post(url, params={"email": existing_email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity. Use another"


def test_unregister_participant_removes_email():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    url = _activity_path(activity_name, "participants")

    # Act
    response = client.delete(url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities_store[activity_name]["participants"]


def test_unregister_for_nonexistent_activity_returns_404():
    # Arrange
    url = _activity_path("Hockey Club", "participants")
    email = "student@mergington.edu"

    # Act
    response = client.delete(url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_missing_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    email = "unknown@mergington.edu"
    url = _activity_path(activity_name, "participants")

    # Act
    response = client.delete(url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
