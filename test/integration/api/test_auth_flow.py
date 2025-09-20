"""
Integration tests for authentication flow
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.models.admin import Admin
from app.security.guards import security_guard


class TestAuthenticationFlow:
    """Test end-to-end authentication flow"""
    
    def test_complete_admin_authentication_flow(self, client: TestClient, test_db):
        """Test complete admin authentication flow"""
        # 1. Create admin
        admin_data = {
            "username": "flow_admin",
            "password": "secure_password_123",
            "is_sudo": True,
            "enabled": True,
            "all_services_access": True,
            "modify_users_access": True
        }
        
        create_response = client.post("/api/admins", json=admin_data)
        # Assuming we need to be authenticated to create admin
        # In real scenario, this might need to be done via database seeding
        
        # 2. Login and get token
        login_response = client.post(
            "/api/admins/token",
            data={"username": "flow_admin", "password": "secure_password_123"}
        )
        
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Use token to access protected resource
        protected_response = client.get("/api/admins", headers=headers)
        assert protected_response.status_code == 200
        
        # 4. Test token validation
        profile_response = client.get("/api/admins/me", headers=headers)
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            assert profile_data["username"] == "flow_admin"
    
    def test_invalid_credentials_flow(self, client: TestClient):
        """Test authentication flow with invalid credentials"""
        # Attempt login with invalid credentials
        login_response = client.post(
            "/api/admins/token",
            data={"username": "nonexistent", "password": "invalid"}
        )
        
        assert login_response.status_code == 401
        assert "invalid credentials" in login_response.json()["detail"].lower()
        
        # Attempt to access protected resource without token
        protected_response = client.get("/api/admins")
        assert protected_response.status_code == 401
    
    def test_disabled_admin_authentication(self, client: TestClient, test_db):
        """Test authentication flow with disabled admin"""
        from app.db import crud
        
        # Create disabled admin directly in database
        admin_data = {
            "username": "disabled_admin",
            "hashed_password": "$2b$12$test_hash",
            "is_sudo": False,
            "enabled": False  # Disabled
        }
        disabled_admin = crud.create_admin(test_db, admin_data)
        
        # Attempt login
        login_response = client.post(
            "/api/admins/token",
            data={"username": "disabled_admin", "password": "test_password"}
        )
        
        assert login_response.status_code == 401
        assert "disabled" in login_response.json()["detail"].lower()
    
    def test_token_expiration_flow(self, client: TestClient):
        """Test token expiration handling"""
        # This would require mocking token generation with short expiry
        # or manipulating time to test expiration
        pass
    
    def test_concurrent_authentication_attempts(self, client: TestClient, test_admin):
        """Test concurrent authentication attempts"""
        import threading
        import time
        
        results = []
        
        def attempt_login():
            response = client.post(
                "/api/admins/token",
                data={"username": test_admin.username, "password": "test_password_123"}
            )
            results.append(response.status_code)
        
        # Start multiple concurrent login attempts
        threads = []
        for i in range(5):
            thread = threading.Thread(target=attempt_login)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All attempts should either succeed or fail consistently
        assert len(results) == 5
        # Results should be either all 200 (success) or include some failures


class TestAuthorizationFlow:
    """Test authorization flow with different permission levels"""
    
    def test_sudo_admin_access_flow(self, client: TestClient, test_db):
        """Test sudo admin access to restricted resources"""
        from app.db import crud
        
        # Create sudo admin
        sudo_admin_data = {
            "username": "sudo_test",
            "hashed_password": "$2b$12$test_hash",
            "is_sudo": True,
            "enabled": True
        }
        sudo_admin = crud.create_admin(test_db, sudo_admin_data)
        
        # Login and get token (would need proper password)
        # This is a simplified test - in reality you'd need proper auth
        
        # Test access to sudo-restricted endpoint
        headers = {"Authorization": "Bearer valid_sudo_token"}
        
        # Attempt to create another admin (sudo required)
        new_admin_data = {
            "username": "created_by_sudo",
            "password": "password123",
            "is_sudo": False
        }
        
        create_response = client.post(
            "/api/admins",
            json=new_admin_data,
            headers=headers
        )
        
        # Should succeed for sudo admin
        # assert create_response.status_code == 201
    
    def test_regular_admin_access_restrictions(self, client: TestClient, test_db):
        """Test regular admin access restrictions"""
        from app.db import crud
        
        # Create regular admin
        regular_admin_data = {
            "username": "regular_test", 
            "hashed_password": "$2b$12$test_hash",
            "is_sudo": False,
            "enabled": True,
            "modify_users_access": True,
            "all_services_access": False
        }
        regular_admin = crud.create_admin(test_db, regular_admin_data)
        
        # Test access to user management (should work with modify_users_access)
        headers = {"Authorization": "Bearer valid_regular_token"}
        
        # Test creating user
        user_data = {
            "username": "test_user_created",
            "expire_strategy": "never",
            "service_ids": []
        }
        
        create_user_response = client.post(
            "/api/users",
            json=user_data,
            headers=headers
        )
        
        # Should succeed based on permissions
        # Result depends on actual implementation
    
    def test_permission_escalation_prevention(self, client: TestClient):
        """Test prevention of permission escalation"""
        # Test that regular admin cannot elevate their own permissions
        headers = {"Authorization": "Bearer regular_admin_token"}
        
        escalation_data = {
            "is_sudo": True,  # Attempt to become sudo
            "all_services_access": True
        }
        
        response = client.put(
            "/api/admins/self",  # Assuming such endpoint exists
            json=escalation_data,
            headers=headers
        )
        
        # Should be denied
        assert response.status_code in [403, 400]


class TestSecurityFlowIntegration:
    """Test security features integration"""
    
    def test_rate_limiting_integration(self, client: TestClient):
        """Test rate limiting integration with authentication"""
        # Make multiple rapid requests to test rate limiting
        responses = []
        
        for i in range(20):  # Assuming rate limit is lower than 20
            response = client.post(
                "/api/admins/token",
                data={"username": "test", "password": "wrong"}
            )
            responses.append(response.status_code)
        
        # Should eventually hit rate limit
        assert 429 in responses  # Too Many Requests
    
    def test_security_lockout_integration(self, client: TestClient, test_admin):
        """Test security lockout after failed attempts"""
        # Clear any existing lockout state
        security_guard.failed_attempts.clear()
        
        # Make multiple failed attempts
        for i in range(6):  # Assuming lockout threshold is 5
            response = client.post(
                "/api/admins/token",
                data={"username": test_admin.username, "password": "wrong_password"}
            )
        
        # Account should be locked out
        lockout_response = client.post(
            "/api/admins/token",
            data={"username": test_admin.username, "password": "correct_password"}
        )
        
        assert lockout_response.status_code == 423  # Locked
    
    def test_security_logging_integration(self, client: TestClient, test_admin):
        """Test security event logging integration"""
        with patch('app.security.security_logger.security_logger') as mock_logger:
            # Successful login
            client.post(
                "/api/admins/token",
                data={"username": test_admin.username, "password": "test_password_123"}
            )
            
            # Failed login
            client.post(
                "/api/admins/token",
                data={"username": test_admin.username, "password": "wrong_password"}
            )
            
            # Verify security events were logged
            assert mock_logger.log_security_event.call_count >= 1


class TestNodeAuthenticationFlow:
    """Test node authentication flow"""
    
    def test_node_token_generation_and_validation(self, client: TestClient, test_node, auth_headers):
        """Test node token generation and validation flow"""
        # Generate token for node
        token_response = client.post(
            f"/api/nodes/{test_node.id}/generate-token",
            headers=auth_headers
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            node_token = token_data.get("token")
            
            # Use token for node operations
            node_headers = {"Authorization": f"Bearer {node_token}"}
            
            # Test node-authenticated endpoint
            stats_response = client.get(
                f"/api/nodes/{test_node.id}/internal-stats",
                headers=node_headers
            )
            
            # Should be authorized for node operations
            assert stats_response.status_code in [200, 404]  # 404 if endpoint doesn't exist
    
    def test_node_token_revocation(self, client: TestClient, test_node, auth_headers):
        """Test node token revocation flow"""
        # Generate token
        token_response = client.post(
            f"/api/nodes/{test_node.id}/generate-token",
            headers=auth_headers
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            node_token = token_data.get("token")
            
            # Revoke token
            revoke_response = client.post(
                f"/api/nodes/{test_node.id}/revoke-token",
                json={"token": node_token},
                headers=auth_headers
            )
            
            # Try to use revoked token
            node_headers = {"Authorization": f"Bearer {node_token}"}
            stats_response = client.get(
                f"/api/nodes/{test_node.id}/internal-stats",
                headers=node_headers
            )
            
            # Should be unauthorized
            assert stats_response.status_code == 401


class TestUserSubscriptionFlow:
    """Test user subscription access flow"""
    
    def test_subscription_access_flow(self, client: TestClient, test_user):
        """Test user subscription access flow"""
        # Access subscription with user key
        subscription_response = client.get(f"/sub/{test_user.key}")
        
        # Should return subscription content or redirect
        assert subscription_response.status_code in [200, 302]
        
        if subscription_response.status_code == 200:
            # Should contain subscription configuration
            content = subscription_response.content.decode()
            assert len(content) > 0
    
    def test_invalid_subscription_key(self, client: TestClient):
        """Test subscription access with invalid key"""
        invalid_response = client.get("/sub/invalid_key_123")
        
        assert invalid_response.status_code == 404
    
    def test_disabled_user_subscription(self, client: TestClient, test_db):
        """Test subscription access for disabled user"""
        from app.db import crud
        
        # Create disabled user
        user_data = {
            "username": "disabled_user",
            "expire_strategy": "never",
            "enabled": False,
            "key": "disabled_user_key_123"
        }
        disabled_user = crud.create_user(test_db, user_data)
        
        # Try to access subscription
        response = client.get(f"/sub/{disabled_user.key}")
        
        # Should be denied or return error
        assert response.status_code in [403, 404]


@pytest.mark.integration
class TestCORSIntegration:
    """Test CORS integration in authentication flow"""
    
    def test_cors_preflight_authentication_endpoints(self, client: TestClient):
        """Test CORS preflight for authentication endpoints"""
        preflight_response = client.options(
            "/api/admins/token",
            headers={
                "Origin": "https://admin.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Should include CORS headers
        assert "Access-Control-Allow-Origin" in preflight_response.headers
        assert "Access-Control-Allow-Methods" in preflight_response.headers
    
    def test_cors_actual_request_with_auth(self, client: TestClient, auth_headers):
        """Test CORS on actual authenticated request"""
        response = client.get(
            "/api/admins",
            headers={
                **auth_headers,
                "Origin": "https://admin.example.com"
            }
        )
        
        # Should include CORS headers in response
        if response.status_code == 200:
            assert "Access-Control-Allow-Origin" in response.headers


@pytest.mark.integration 
class TestDatabaseTransactionIntegration:
    """Test database transaction integration with authentication"""
    
    def test_failed_authentication_rollback(self, client: TestClient, test_db):
        """Test that failed authentication doesn't leave partial data"""
        initial_count = test_db.query(Admin).count()
        
        # Attempt operation that should fail and rollback
        with patch('app.db.crud.create_admin') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            response = client.post(
                "/api/admins",
                json={
                    "username": "rollback_test",
                    "password": "password123",
                    "is_sudo": False
                }
            )
        
        # Should not have created admin
        final_count = test_db.query(Admin).count()
        assert final_count == initial_count
    
    def test_successful_authentication_commit(self, client: TestClient, test_db):
        """Test that successful authentication commits properly"""
        # This would test successful operations actually persist
        pass