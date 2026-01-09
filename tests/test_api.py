"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = copy.deepcopy(activities)
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert isinstance(data["Chess Club"], dict)
        assert "description" in data["Chess Club"]
        assert "schedule" in data["Chess Club"]
        assert "max_participants" in data["Chess Club"]
        assert "participants" in data["Chess Club"]
    
    def test_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signups are prevented"""
        email = "test@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_with_special_characters(self, client):
        """Test signup with email containing special characters"""
        from urllib.parse import quote
        
        email = "test.student+special@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/signup?email={quote(email)}"
        )
        
        assert response.status_code == 200
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        # First, add a participant
        email = "remove.test@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Now remove them
        response = client.delete(
            f"/activities/Chess Club/participants/{email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert email in data["message"]
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Chess Club"]["participants"]
    
    def test_remove_nonexistent_participant(self, client):
        """Test removing a participant that isn't registered"""
        response = client.delete(
            "/activities/Chess Club/participants/notregistered@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_remove_from_nonexistent_activity(self, client):
        """Test removing a participant from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/participants/student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_remove_existing_participant(self, client):
        """Test removing a participant that was there from the start"""
        # Michael is already in Chess Club
        email = "michael@mergington.edu"
        
        response = client.delete(
            f"/activities/Chess Club/participants/{email}"
        )
        
        assert response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for root endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_signup_and_remove_workflow(self, client):
        """Test complete workflow of signing up and removing a participant"""
        email = "workflow.test@mergington.edu"
        activity = "Tennis Club"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify added
        after_signup = client.get("/activities")
        new_count = len(after_signup.json()[activity]["participants"])
        assert new_count == initial_count + 1
        assert email in after_signup.json()[activity]["participants"]
        
        # Remove
        remove_response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert remove_response.status_code == 200
        
        # Verify removed
        after_remove = client.get("/activities")
        final_count = len(after_remove.json()[activity]["participants"])
        assert final_count == initial_count
        assert email not in after_remove.json()[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client):
        """Test signing up for multiple activities"""
        email = "multi.activity@mergington.edu"
        
        # Sign up for multiple activities
        activities_to_join = ["Chess Club", "Programming Class", "Tennis Club"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify participant is in all activities
        all_activities = client.get("/activities").json()
        
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
