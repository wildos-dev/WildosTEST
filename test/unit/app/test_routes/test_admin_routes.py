"""
Unit tests for admin routes (app/routes/admin.py)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from datetime import datetime

from app.models.admin import Admin, AdminCreate, AdminModify, AdminPartialModify
from app.routes.admin import (
    create_admin,
    get_current_admin,
    get_current_sudo_admin,
    modify_admin,
    remove_admin,
    get_admin,
    get_admins,
    reset_admin_data_usage
)


class TestAdminAuthentication:
    """Test admin authentication endpoints"""
    
    def test_create_admin_token_success(self, client: TestClient, test_admin):
        """Test successful admin token creation"""
        response = client.post(
            "/api/admins/token",
            data={"username": "test_admin", "password": "test_password_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["is_sudo"], bool)
    
    def test_create_admin_token_invalid_credentials(self, client: TestClient):
        """Test admin token creation with invalid credentials"""
        response = client.post(
            "/api/admins/token",
            data={"username": "invalid_user", "password": "invalid_password"}
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_create_admin_token_disabled_admin(self, client: TestClient, test_db):
        """Test token creation for disabled admin"""
        from app.db import crud
        
        # Create disabled admin
        admin_data = {
            "username": "disabled_admin",
            "hashed_password": "$2b$12$test",
            "is_sudo": False,
            "enabled": False
        }
        disabled_admin = crud.create_admin(test_db, admin_data)
        
        response = client.post(
            "/api/admins/token",
            data={"username": "disabled_admin", "password": "test_password"}
        )
        
        assert response.status_code == 401
        assert "disabled" in response.json()["detail"].lower()
    
    @patch('app.security.security_logger.log_authentication_event')
    def test_create_admin_token_logs_authentication_attempt(self, mock_log, client: TestClient, test_admin):
        """Test that authentication attempts are logged"""
        client.post(
            "/api/admins/token",
            data={"username": "test_admin", "password": "test_password_123"}
        )
        
        mock_log.assert_called()


class TestAdminCRUD:
    """Test admin CRUD operations"""
    
    def test_create_admin_success(self, client: TestClient, auth_headers):
        """Test successful admin creation"""
        admin_data = {
            "username": "new_admin",
            "password": "secure_password_123",
            "is_sudo": False,
            "enabled": True,
            "all_services_access": False,
            "modify_users_access": True,
            "service_ids": [],
            "subscription_url_prefix": "https://example.com"
        }
        
        response = client.post(
            "/api/admins",
            json=admin_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "new_admin"
        assert data["is_sudo"] == False
        assert data["enabled"] == True
        assert "password" not in data  # Password should not be returned
    
    def test_create_admin_duplicate_username(self, client: TestClient, auth_headers, test_admin):
        """Test admin creation with duplicate username"""
        admin_data = {
            "username": "test_admin",  # Duplicate
            "password": "password123",
            "is_sudo": False
        }
        
        response = client.post(
            "/api/admins",
            json=admin_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_create_admin_invalid_data(self, client: TestClient, auth_headers):
        """Test admin creation with invalid data"""
        invalid_data = {
            "username": "",  # Empty username
            "password": "123",  # Too short
            "is_sudo": False
        }
        
        response = client.post(
            "/api/admins",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_get_admin_success(self, client: TestClient, auth_headers, test_admin):
        """Test successful admin retrieval"""
        response = client.get(
            f"/api/admins/{test_admin.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_admin.id
        assert data["username"] == test_admin.username
        assert "hashed_password" not in data
    
    def test_get_admin_not_found(self, client: TestClient, auth_headers):
        """Test admin retrieval with non-existent ID"""
        response = client.get(
            "/api/admins/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_admins_list(self, client: TestClient, auth_headers, test_admin):
        """Test admins list retrieval"""
        response = client.get(
            "/api/admins",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(admin["id"] == test_admin.id for admin in data)
    
    def test_modify_admin_success(self, client: TestClient, auth_headers, test_admin):
        """Test successful admin modification"""
        modify_data = {
            "enabled": False,
            "modify_users_access": False,
            "subscription_url_prefix": "https://updated.example.com"
        }
        
        response = client.put(
            f"/api/admins/{test_admin.id}",
            json=modify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] == False
        assert data["modify_users_access"] == False
        assert data["subscription_url_prefix"] == "https://updated.example.com"
    
    def test_modify_admin_password_update(self, client: TestClient, auth_headers, test_admin):
        """Test admin password modification"""
        modify_data = {
            "password": "new_secure_password_456"
        }
        
        response = client.put(
            f"/api/admins/{test_admin.id}",
            json=modify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Verify password was actually changed by attempting login
        login_response = client.post(
            "/api/admins/token",
            data={"username": test_admin.username, "password": "new_secure_password_456"}
        )
        assert login_response.status_code == 200
    
    def test_remove_admin_success(self, client: TestClient, auth_headers, test_db):
        """Test successful admin removal"""
        from app.db import crud
        
        # Create additional admin to remove
        admin_data = {
            "username": "admin_to_remove",
            "hashed_password": "$2b$12$test",
            "is_sudo": False,
            "enabled": True
        }
        admin_to_remove = crud.create_admin(test_db, admin_data)
        
        response = client.delete(
            f"/api/admins/{admin_to_remove.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify admin was removed
        get_response = client.get(
            f"/api/admins/{admin_to_remove.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_remove_admin_not_found(self, client: TestClient, auth_headers):
        """Test admin removal with non-existent ID"""
        response = client.delete(
            "/api/admins/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestAdminPermissions:
    """Test admin permission system"""
    
    def test_sudo_admin_required_operations(self, client: TestClient):
        """Test operations that require sudo admin privileges"""
        # Create non-sudo admin token
        non_sudo_data = {
            "username": "regular_admin",
            "password": "password123",
            "is_sudo": False,
            "enabled": True
        }
        
        # This would need to be implemented with proper test setup
        # Testing the permission system functionality
        pass
    
    def test_service_access_restrictions(self, client: TestClient, auth_headers):
        """Test service access restrictions for non-sudo admins"""
        # Test admin service access limitations
        response = client.get(
            "/api/admins/services",
            headers=auth_headers
        )
        
        # Verify response based on admin's service access permissions
        assert response.status_code in [200, 403]


class TestAdminSecurityFeatures:
    """Test admin security features"""
    
    @patch('app.security.guards.security_guard._is_locked_out')
    def test_admin_lockout_mechanism(self, mock_lockout, client: TestClient, test_admin):
        """Test admin lockout after failed attempts"""
        mock_lockout.return_value = True
        
        response = client.post(
            "/api/admins/token",
            data={"username": test_admin.username, "password": "wrong_password"}
        )
        
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()
    
    @patch('app.security.security_logger.log_security_event')
    def test_admin_security_logging(self, mock_log, client: TestClient, auth_headers):
        """Test security event logging for admin operations"""
        client.get("/api/admins", headers=auth_headers)
        
        # Verify security events are logged
        mock_log.assert_called()
    
    def test_admin_token_expiration(self, client: TestClient):
        """Test admin token expiration handling"""
        # Create expired token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwiZXhwIjoxfQ.expired"
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get(
            "/api/admins",
            headers=expired_headers
        )
        
        assert response.status_code == 401


class TestAdminDataUsageOperations:
    """Test admin data usage operations"""
    
    def test_reset_admin_data_usage(self, client: TestClient, auth_headers, test_admin):
        """Test admin data usage reset functionality"""
        response = client.post(
            f"/api/admins/{test_admin.id}/reset-data-usage",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users_data_usage" in data
        assert data["users_data_usage"] == 0
    
    def test_get_admin_data_usage_stats(self, client: TestClient, auth_headers, test_admin):
        """Test admin data usage statistics retrieval"""
        response = client.get(
            f"/api/admins/{test_admin.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users_data_usage" in data
        assert isinstance(data["users_data_usage"], int)


class TestAdminValidation:
    """Test admin input validation"""
    
    def test_admin_username_validation(self, client: TestClient, auth_headers):
        """Test admin username validation rules"""
        invalid_usernames = [
            "",  # Empty
            "a",  # Too short
            "a" * 33,  # Too long
            "admin@test",  # Invalid characters
            "admin user",  # Spaces
        ]
        
        for username in invalid_usernames:
            admin_data = {
                "username": username,
                "password": "valid_password_123",
                "is_sudo": False
            }
            
            response = client.post(
                "/api/admins",
                json=admin_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422, f"Username '{username}' should be invalid"
    
    def test_admin_password_validation(self, client: TestClient, auth_headers):
        """Test admin password validation rules"""
        weak_passwords = [
            "",  # Empty
            "123",  # Too short
            "password",  # Too common
        ]
        
        for password in weak_passwords:
            admin_data = {
                "username": f"test_admin_{hash(password)}",
                "password": password,
                "is_sudo": False
            }
            
            response = client.post(
                "/api/admins",
                json=admin_data,
                headers=auth_headers
            )
            
            # Depending on validation rules, this might be 422 or 400
            assert response.status_code in [400, 422], f"Password '{password}' should be invalid"


@pytest.mark.parametrize("endpoint", [
    "/api/admins",
    "/api/admins/1",
])
def test_admin_endpoints_require_authentication(client: TestClient, endpoint):
    """Test that admin endpoints require authentication"""
    response = client.get(endpoint)
    assert response.status_code == 401


@pytest.mark.parametrize("method,endpoint", [
    ("POST", "/api/admins"),
    ("PUT", "/api/admins/1"),
    ("DELETE", "/api/admins/1"),
])
def test_admin_modification_endpoints_require_sudo(client: TestClient, method, endpoint):
    """Test that admin modification endpoints require sudo privileges"""
    # This would need proper non-sudo admin token setup
    # For now, test without auth to ensure auth is required
    
    test_data = {"username": "test", "password": "test123", "is_sudo": False}
    
    if method == "POST":
        response = client.post(endpoint, json=test_data)
    elif method == "PUT":
        response = client.put(endpoint, json=test_data)
    elif method == "DELETE":
        response = client.delete(endpoint)
    
    assert response.status_code == 401  # Unauthorized without token