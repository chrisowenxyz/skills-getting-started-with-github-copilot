"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_activities(monkeypatch):
    """
    Fixture that provides isolated test activities.
    Replaces the global activities dict for the duration of the test.
    """
    test_activities = {
        "Test Activity 1": {
            "description": "A test activity",
            "schedule": "Monday, 3:00 PM - 4:00 PM",
            "max_participants": 5,
            "participants": ["alice@test.edu", "bob@test.edu"]
        },
        "Test Activity 2": {
            "description": "Another test activity",
            "schedule": "Wednesday, 2:00 PM - 3:00 PM",
            "max_participants": 2,
            "participants": ["charlie@test.edu"]
        }
    }
    
    # Replace the module-level activities dict
    import src.app
    monkeypatch.setattr(src.app, "activities", test_activities)
    
    return test_activities


# ===== HAPPY PATH TESTS =====

def test_get_activities(client, mock_activities):
    """Test GET /activities returns all activities"""
    response = client.get("/activities")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert "Test Activity 1" in data
    assert "Test Activity 2" in data
    
    # Verify structure
    activity1 = data["Test Activity 1"]
    assert activity1["description"] == "A test activity"
    assert activity1["max_participants"] == 5
    assert len(activity1["participants"]) == 2


def test_signup_new_student(client, mock_activities):
    """Test POST /signup successfully registers a new student"""
    response = client.post(
        "/activities/Test Activity 1/signup?email=david@test.edu"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Signed up david@test.edu for Test Activity 1"
    
    # Verify participant was added
    assert "david@test.edu" in mock_activities["Test Activity 1"]["participants"]
    assert len(mock_activities["Test Activity 1"]["participants"]) == 3


def test_remove_participant(client, mock_activities):
    """Test POST /remove successfully removes a participant"""
    response = client.post(
        "/activities/Test Activity 1/remove?email=alice@test.edu"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Removed alice@test.edu from Test Activity 1"
    
    # Verify participant was removed
    assert "alice@test.edu" not in mock_activities["Test Activity 1"]["participants"]
    assert len(mock_activities["Test Activity 1"]["participants"]) == 1


def test_redirect_root(client):
    """Test GET / redirects to /static/index.html"""
    response = client.get("/", follow_redirects=False)
    
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"


# ===== ERROR CASE TESTS =====

def test_signup_nonexistent_activity(client, mock_activities):
    """Test signup for non-existent activity returns 404"""
    response = client.post(
        "/activities/Nonexistent Activity/signup?email=test@test.edu"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_duplicate_student(client, mock_activities):
    """Test signup for already-registered student returns 400"""
    response = client.post(
        "/activities/Test Activity 1/signup?email=alice@test.edu"
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Student already signed up"


def test_remove_nonexistent_activity(client, mock_activities):
    """Test remove from non-existent activity returns 404"""
    response = client.post(
        "/activities/Nonexistent Activity/remove?email=test@test.edu"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_remove_student_not_enrolled(client, mock_activities):
    """Test removing student not enrolled returns 400"""
    response = client.post(
        "/activities/Test Activity 1/remove?email=notregistered@test.edu"
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Student not signed up for this activity"


def test_signup_at_max_capacity(client, mock_activities):
    """Test signup when activity is at max capacity"""
    # Test Activity 2 has max_participants=2 and 1 participant
    # Add one more to reach capacity
    response = client.post(
        "/activities/Test Activity 2/signup?email=david@test.edu"
    )
    assert response.status_code == 200
    
    # Now try to add another when at capacity - should still succeed
    # (current implementation doesn't validate max capacity)
    response = client.post(
        "/activities/Test Activity 2/signup?email=emma@test.edu"
    )
    # This test documents current behavior - can be updated when capacity check is added
    assert response.status_code == 200
