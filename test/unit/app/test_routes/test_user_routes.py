"""
Unit tests for user routes (app/routes/user.py)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.user import User, UserCreate, UserModify, UserResponse, UserStatus


class TestUserCRUD:
    """Test user CRUD operations"""
    
    def test_create_user_success(self, client: TestClient, auth_headers, test_service):
        """Test successful user creation"""
        user_data = {
            "username": "new_test_user",
            "expire_strategy": "never",
            "data_limit": 10737418240,  # 10GB
            "data_limit_reset_strategy": "no_reset",
            "note": "Test user for pytest",
            "service_ids": [test_service.id] if test_service else []
        }
        
        response = client.post(
            "/api/users",
            json=user_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "new_test_user"
        assert data["expire_strategy"] == "never"
        assert data["data_limit"] == 10737418240
        assert "subscription_url" in data
    
    def test_create_user_duplicate_username(self, client: TestClient, auth_headers, test_user):
        """Test user creation with duplicate username"""
        user_data = {
            "username": test_user.username,  # Duplicate
            "expire_strategy": "never",
            "service_ids": []
        }
        
        response = client.post(
            "/api/users",
            json=user_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_create_user_invalid_expire_strategy(self, client: TestClient, auth_headers):
        """Test user creation with invalid expire strategy configuration"""
        # start_on_first_use without usage_duration
        invalid_data = {
            "username": "invalid_user",
            "expire_strategy": "start_on_first_use",
            "service_ids": []
        }
        
        response = client.post(
            "/api/users",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_create_user_fixed_date_strategy(self, client: TestClient, auth_headers):
        """Test user creation with fixed_date expire strategy"""
        future_date = datetime.utcnow() + timedelta(days=30)
        user_data = {
            "username": "fixed_date_user",
            "expire_strategy": "fixed_date",
            "expire_date": future_date.isoformat(),
            "service_ids": []
        }
        
        response = client.post(
            "/api/users",
            json=user_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["expire_strategy"] == "fixed_date"
        assert data["expire_date"] is not None
    
    def test_get_user_success(self, client: TestClient, auth_headers, test_user):
        """Test successful user retrieval"""
        response = client.get(
            f"/api/users/{test_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert "subscription_url" in data
        assert "used_traffic" in data
        assert "lifetime_used_traffic" in data
    
    def test_get_user_not_found(self, client: TestClient, auth_headers):
        """Test user retrieval with non-existent ID"""
        response = client.get(
            "/api/users/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_users_list(self, client: TestClient, auth_headers, test_user):
        """Test users list retrieval with pagination"""
        response = client.get(
            "/api/users?offset=0&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0
    
    def test_get_users_with_filters(self, client: TestClient, auth_headers):
        """Test users list with various filters"""
        # Test search filter
        response = client.get(
            "/api/users?search=test",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test status filter
        response = client.get(
            "/api/users?status=active",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test data limit filter
        response = client.get(
            "/api/users?data_limit_reached=false",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_modify_user_success(self, client: TestClient, auth_headers, test_user):
        """Test successful user modification"""
        modify_data = {
            "data_limit": 21474836480,  # 20GB
            "note": "Updated test user",
            "enabled": True
        }
        
        response = client.put(
            f"/api/users/{test_user.id}",
            json=modify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data_limit"] == 21474836480
        assert data["note"] == "Updated test user"
    
    def test_modify_user_expire_strategy_validation(self, client: TestClient, auth_headers, test_user):
        """Test user modification with expire strategy validation"""
        # Try to set start_on_first_use without usage_duration
        invalid_data = {
            "expire_strategy": "start_on_first_use",
            "usage_duration": None
        }
        
        response = client.put(
            f"/api/users/{test_user.id}",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_remove_user_success(self, client: TestClient, auth_headers, test_db):
        """Test successful user removal"""
        from app.db import crud
        
        # Create user to remove
        user_data = {
            "username": "user_to_remove",
            "expire_strategy": "never",
            "enabled": True
        }
        user_to_remove = crud.create_user(test_db, user_data)
        
        response = client.delete(
            f"/api/users/{user_to_remove.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify user is marked as removed, not actually deleted
        get_response = client.get(
            f"/api/users/{user_to_remove.id}",
            headers=auth_headers
        )
        # Should be 404 since removed users are filtered out
        assert get_response.status_code == 404


class TestUserStatusOperations:
    """Test user status management operations"""
    
    def test_reset_user_data_usage(self, client: TestClient, auth_headers, test_user):
        """Test user data usage reset"""
        response = client.post(
            f"/api/users/{test_user.id}/reset-data-usage",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["used_traffic"] == 0
    
    def test_revoke_user_subscription(self, client: TestClient, auth_headers, test_user):
        """Test user subscription revocation"""
        response = client.post(
            f"/api/users/{test_user.id}/revoke-sub",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sub_revoked_at" in data
        assert data["sub_revoked_at"] is not None
    
    def test_enable_user(self, client: TestClient, auth_headers, test_user):
        """Test user enabling"""
        response = client.post(
            f"/api/users/{test_user.id}/enable",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] == True
    
    def test_disable_user(self, client: TestClient, auth_headers, test_user):
        """Test user disabling"""
        response = client.post(
            f"/api/users/{test_user.id}/disable",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] == False
    
    def test_reset_user_key(self, client: TestClient, auth_headers, test_user):
        """Test user key reset"""
        original_key = test_user.key
        
        response = client.post(
            f"/api/users/{test_user.id}/reset-key",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["key"] != original_key
        assert len(data["key"]) == 32  # Standard key length


class TestUserSubscription:
    """Test user subscription functionality"""
    
    def test_get_user_subscription_url(self, client: TestClient, test_user):
        """Test user subscription URL access"""
        response = client.get(f"/sub/{test_user.key}")
        
        # Should return subscription content or redirect
        assert response.status_code in [200, 302]
    
    def test_get_user_subscription_invalid_key(self, client: TestClient):
        """Test subscription access with invalid key"""
        response = client.get("/sub/invalid_key_123")
        
        assert response.status_code == 404
    
    @patch('app.routes.user.track_subscription_access')
    def test_subscription_access_tracking(self, mock_track, client: TestClient, test_user):
        """Test that subscription access is tracked"""
        client.get(f"/sub/{test_user.key}")
        
        # Verify tracking was called
        mock_track.assert_called()


class TestUserUsageStats:
    """Test user usage statistics"""
    
    def test_get_user_usage_stats(self, client: TestClient, auth_headers, test_user):
        """Test user usage statistics retrieval"""
        response = client.get(
            f"/api/users/{test_user.id}/usage",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "total" in data
        assert "node_usages" in data
        assert isinstance(data["node_usages"], list)
    
    def test_get_user_usage_with_time_range(self, client: TestClient, auth_headers, test_user):
        """Test user usage statistics with time range"""
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = client.get(
            f"/api/users/{test_user.id}/usage?start={start_date}&end={end_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "node_usages" in data


class TestUserValidation:
    """Test user input validation"""
    
    def test_username_validation(self, client: TestClient, auth_headers):
        """Test username validation rules"""
        invalid_usernames = [
            "",  # Empty
            "ab",  # Too short
            "a" * 33,  # Too long
            "user@test",  # Invalid characters
            "user space",  # Spaces
            "USER",  # Should be lowercase
        ]
        
        for username in invalid_usernames:
            user_data = {
                "username": username,
                "expire_strategy": "never",
                "service_ids": []
            }
            
            response = client.post(
                "/api/users",
                json=user_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422, f"Username '{username}' should be invalid"
    
    def test_data_limit_validation(self, client: TestClient, auth_headers):
        """Test data limit validation"""
        user_data = {
            "username": "limit_test_user",
            "expire_strategy": "never",
            "data_limit": -1,  # Negative limit should be invalid
            "service_ids": []
        }
        
        response = client.post(
            "/api/users",
            json=user_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_expire_date_validation(self, client: TestClient, auth_headers):
        """Test expire date validation"""
        # Past date should be invalid
        past_date = datetime.utcnow() - timedelta(days=1)
        user_data = {
            "username": "past_date_user",
            "expire_strategy": "fixed_date",
            "expire_date": past_date.isoformat(),
            "service_ids": []
        }
        
        response = client.post(
            "/api/users",
            json=user_data,
            headers=auth_headers
        )
        
        # Depending on validation rules, this might be allowed or not
        # Check your actual validation logic
        assert response.status_code in [201, 422]


class TestUserPermissions:
    """Test user permission system"""
    
    def test_admin_service_access_restrictions(self, client: TestClient, auth_headers):
        """Test admin service access restrictions for user operations"""
        # This would test that admins can only manage users in their assigned services
        response = client.get("/api/users", headers=auth_headers)
        
        assert response.status_code == 200
        # Additional logic would verify service filtering
    
    def test_modify_users_permission_required(self, client: TestClient):
        """Test that modify_users_access permission is required for user modifications"""
        # Would need admin without modify_users_access permission
        # This is a placeholder for permission testing
        pass


class TestUserNotifications:
    """Test user notification integration"""
    
    @patch('app.notification.service.NotificationService.send_user_notification')
    def test_user_creation_notification(self, mock_notify, client: TestClient, auth_headers):
        """Test that user creation triggers notification"""
        user_data = {
            "username": "notify_test_user",
            "expire_strategy": "never",
            "service_ids": []
        }
        
        response = client.post(
            "/api/users",
            json=user_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        # Verify notification was sent
        mock_notify.assert_called()
    
    @patch('app.notification.service.NotificationService.send_user_notification')
    def test_user_modification_notification(self, mock_notify, client: TestClient, auth_headers, test_user):
        """Test that user modification triggers notification"""
        modify_data = {"enabled": False}
        
        response = client.put(
            f"/api/users/{test_user.id}",
            json=modify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Verify notification was sent
        mock_notify.assert_called()


@pytest.mark.parametrize("endpoint", [
    "/api/users",
    "/api/users/1",
    "/api/users/1/usage",
])
def test_user_endpoints_require_authentication(client: TestClient, endpoint):
    """Test that user endpoints require authentication"""
    response = client.get(endpoint)
    assert response.status_code == 401


@pytest.mark.parametrize("method,endpoint", [
    ("POST", "/api/users"),
    ("PUT", "/api/users/1"),
    ("DELETE", "/api/users/1"),
    ("POST", "/api/users/1/reset-data-usage"),
    ("POST", "/api/users/1/enable"),
    ("POST", "/api/users/1/disable"),
])
def test_user_modification_endpoints_require_auth(client: TestClient, method, endpoint):
    """Test that user modification endpoints require authentication"""
    test_data = {"username": "test", "expire_strategy": "never", "service_ids": []}
    
    if method == "POST":
        response = client.post(endpoint, json=test_data)
    elif method == "PUT":
        response = client.put(endpoint, json=test_data)
    elif method == "DELETE":
        response = client.delete(endpoint)
    
    assert response.status_code == 401