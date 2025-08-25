import pytest
from fastapi.testclient import TestClient

from app.core.security import verify_password


class TestAuth:
    """Test authentication endpoints."""
    
    def test_register_user(self, client: TestClient, sample_user_data):
        """Test user registration."""
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert data["role"] == sample_user_data["role"]
        assert "id" in data
    
    def test_register_duplicate_email(self, client: TestClient, sample_user_data, test_user):
        """Test registration with duplicate email."""
        sample_user_data["email"] = test_user.email
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client: TestClient, sample_user_data, test_user):
        """Test registration with duplicate username."""
        sample_user_data["username"] = test_user.username
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]
    
    def test_login_with_username(self, client: TestClient, test_user):
        """Test login with username."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.username, "password": "testpassword"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_email(self, client: TestClient, test_user):
        """Test login with email."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "testpassword"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.username, "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client: TestClient, auth_headers, test_user):
        """Test getting current user profile."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403
    
    def test_change_password(self, client: TestClient, auth_headers, test_user, db_session):
        """Test changing password."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpassword",
                "new_password": "newtestpassword"
            }
        )
        assert response.status_code == 200
        
        # Verify password was changed
        db_session.refresh(test_user)
        assert verify_password("newtestpassword", test_user.hashed_password)
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """Test changing password with wrong current password."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newtestpassword"
            }
        )
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]
    
    def test_refresh_token(self, client: TestClient, test_user):
        """Test token refresh."""
        # First login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.username, "password": "testpassword"}
        )
        tokens = login_response.json()
        
        # Use refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 200
        
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]
    
    def test_logout(self, client: TestClient, auth_headers):
        """Test logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert "logged out" in response.json()["message"]
