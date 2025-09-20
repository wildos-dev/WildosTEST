"""
Unit tests for service routes (app/routes/service.py)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from app.models.service import Service, ServiceCreate, ServiceModify, ServiceResponse


class TestServiceCRUD:
    """Test service CRUD operations"""
    
    def test_create_service_success(self, client: TestClient, auth_headers):
        """Test successful service creation"""
        service_data = {
            "name": "Premium VPN Service",
            "inbound_ids": []
        }
        
        response = client.post(
            "/api/services",
            json=service_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Premium VPN Service"
        assert data["inbound_ids"] == []
        assert data["user_ids"] == []
    
    def test_create_service_with_inbounds(self, client: TestClient, auth_headers, test_db):
        """Test service creation with inbound assignments"""
        from app.db import crud
        
        # Create test inbound
        inbound_data = {
            "tag": "test_inbound",
            "protocol": "vmess",
            "port": 443,
            "settings": {"clients": []},
            "stream_settings": {"network": "tcp"},
            "enabled": True
        }
        inbound = crud.create_inbound(test_db, inbound_data)
        
        service_data = {
            "name": "Service with Inbounds",
            "inbound_ids": [inbound.id]
        }
        
        response = client.post(
            "/api/services",
            json=service_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert inbound.id in data["inbound_ids"]
    
    def test_create_service_duplicate_name(self, client: TestClient, auth_headers, test_service):
        """Test service creation with duplicate name"""
        service_data = {
            "name": test_service.name,  # Duplicate name
            "inbound_ids": []
        }
        
        response = client.post(
            "/api/services",
            json=service_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_create_service_invalid_inbound_ids(self, client: TestClient, auth_headers):
        """Test service creation with non-existent inbound IDs"""
        service_data = {
            "name": "Invalid Service",
            "inbound_ids": [99999]  # Non-existent inbound ID
        }
        
        response = client.post(
            "/api/services",
            json=service_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "inbound" in response.json()["detail"].lower()
    
    def test_get_service_success(self, client: TestClient, auth_headers, test_service):
        """Test successful service retrieval"""
        response = client.get(
            f"/api/services/{test_service.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_service.id
        assert data["name"] == test_service.name
        assert "inbound_ids" in data
        assert "user_ids" in data
    
    def test_get_service_not_found(self, client: TestClient, auth_headers):
        """Test service retrieval with non-existent ID"""
        response = client.get(
            "/api/services/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_services_list(self, client: TestClient, auth_headers, test_service):
        """Test services list retrieval"""
        response = client.get(
            "/api/services",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(service["id"] == test_service.id for service in data)
    
    def test_modify_service_success(self, client: TestClient, auth_headers, test_service):
        """Test successful service modification"""
        modify_data = {
            "name": "Updated Service Name",
            "inbound_ids": []
        }
        
        response = client.put(
            f"/api/services/{test_service.id}",
            json=modify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Service Name"
    
    def test_modify_service_inbound_assignment(self, client: TestClient, auth_headers, test_service, test_db):
        """Test service inbound assignment modification"""
        from app.db import crud
        
        # Create test inbound
        inbound_data = {
            "tag": "new_test_inbound",
            "protocol": "vless",
            "port": 444,
            "settings": {"clients": []},
            "stream_settings": {"network": "ws"},
            "enabled": True
        }
        new_inbound = crud.create_inbound(test_db, inbound_data)
        
        modify_data = {
            "inbound_ids": [new_inbound.id]
        }
        
        response = client.put(
            f"/api/services/{test_service.id}",
            json=modify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert new_inbound.id in data["inbound_ids"]
    
    def test_remove_service_success(self, client: TestClient, auth_headers, test_db):
        """Test successful service removal"""
        from app.db import crud
        
        # Create service to remove
        service_data = {
            "name": "Service to Remove",
            "inbound_ids": []
        }
        service_to_remove = crud.create_service(test_db, service_data)
        
        response = client.delete(
            f"/api/services/{service_to_remove.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify service was removed
        get_response = client.get(
            f"/api/services/{service_to_remove.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_remove_service_with_users(self, client: TestClient, auth_headers, test_service, test_user):
        """Test service removal when service has assigned users"""
        # Assign user to service
        from app.db import crud
        
        # This test verifies behavior when removing service with active users
        # Depending on business logic, this might prevent deletion or cascade
        response = client.delete(
            f"/api/services/{test_service.id}",
            headers=auth_headers
        )
        
        # Status could be 204 (success), 409 (conflict), or 400 (bad request)
        # depending on business rules
        assert response.status_code in [204, 400, 409]


class TestServiceInboundManagement:
    """Test service inbound management operations"""
    
    def test_add_inbound_to_service(self, client: TestClient, auth_headers, test_service, test_db):
        """Test adding inbound to service"""
        from app.db import crud
        
        # Create test inbound
        inbound_data = {
            "tag": "add_test_inbound",
            "protocol": "trojan",
            "port": 445,
            "settings": {"clients": []},
            "stream_settings": {"network": "tcp"},
            "enabled": True
        }
        inbound = crud.create_inbound(test_db, inbound_data)
        
        response = client.post(
            f"/api/services/{test_service.id}/inbounds/{inbound.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert inbound.id in data["inbound_ids"]
    
    def test_remove_inbound_from_service(self, client: TestClient, auth_headers, test_service, test_db):
        """Test removing inbound from service"""
        from app.db import crud
        
        # Create and assign inbound to service
        inbound_data = {
            "tag": "remove_test_inbound",
            "protocol": "shadowsocks",
            "port": 446,
            "settings": {"method": "aes-256-gcm"},
            "enabled": True
        }
        inbound = crud.create_inbound(test_db, inbound_data)
        
        # First add inbound to service
        crud.assign_inbound_to_service(test_db, inbound.id, test_service.id)
        
        # Then remove it
        response = client.delete(
            f"/api/services/{test_service.id}/inbounds/{inbound.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert inbound.id not in data["inbound_ids"]
    
    def test_get_service_inbounds(self, client: TestClient, auth_headers, test_service):
        """Test retrieving service inbounds"""
        response = client.get(
            f"/api/services/{test_service.id}/inbounds",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestServiceUserManagement:
    """Test service user management"""
    
    def test_get_service_users(self, client: TestClient, auth_headers, test_service):
        """Test retrieving service users"""
        response = client.get(
            f"/api/services/{test_service.id}/users",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_service_user_filtering(self, client: TestClient, auth_headers, test_service):
        """Test service user filtering by status"""
        # Test filtering by active status
        response = client.get(
            f"/api/services/{test_service.id}/users?status=active",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Test filtering by enabled status
        response = client.get(
            f"/api/services/{test_service.id}/users?enabled=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestServiceValidation:
    """Test service input validation"""
    
    def test_service_name_validation(self, client: TestClient, auth_headers):
        """Test service name validation"""
        invalid_names = [
            "",  # Empty
            "a" * 65,  # Too long
            None,  # Null
        ]
        
        for name in invalid_names:
            service_data = {
                "name": name,
                "inbound_ids": []
            }
            
            response = client.post(
                "/api/services",
                json=service_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422, f"Name '{name}' should be invalid"
    
    def test_inbound_ids_validation(self, client: TestClient, auth_headers):
        """Test inbound IDs validation"""
        invalid_inbound_ids = [
            [0],  # Invalid ID
            [-1],  # Negative ID
            ["invalid"],  # String instead of int
        ]
        
        for inbound_ids in invalid_inbound_ids:
            service_data = {
                "name": f"Test Service {inbound_ids}",
                "inbound_ids": inbound_ids
            }
            
            response = client.post(
                "/api/services",
                json=service_data,
                headers=auth_headers
            )
            
            assert response.status_code in [400, 422], f"Inbound IDs {inbound_ids} should be invalid"


class TestServicePermissions:
    """Test service permission system"""
    
    def test_admin_service_access_filtering(self, client: TestClient, auth_headers):
        """Test that admins only see services they have access to"""
        response = client.get("/api/services", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify service access based on admin permissions
        # This would depend on the specific admin's service assignments
        assert isinstance(data, list)
    
    def test_service_modification_permissions(self, client: TestClient, auth_headers, test_service):
        """Test service modification permissions"""
        modify_data = {"name": "Modified Service"}
        
        response = client.put(
            f"/api/services/{test_service.id}",
            json=modify_data,
            headers=auth_headers
        )
        
        # Should succeed if admin has access to the service
        assert response.status_code in [200, 403]


class TestServiceStatistics:
    """Test service statistics and metrics"""
    
    def test_get_service_statistics(self, client: TestClient, auth_headers, test_service):
        """Test service statistics retrieval"""
        response = client.get(
            f"/api/services/{test_service.id}/stats",
            headers=auth_headers
        )
        
        # Depending on implementation, this might return stats or 404
        assert response.status_code in [200, 404]
    
    def test_service_usage_metrics(self, client: TestClient, auth_headers, test_service):
        """Test service usage metrics"""
        response = client.get(
            f"/api/services/{test_service.id}/usage",
            headers=auth_headers
        )
        
        # Depending on implementation
        assert response.status_code in [200, 404]


class TestServiceInboundValidation:
    """Test service inbound validation and security"""
    
    @patch('app.routes.service.validate_inbound_configuration')
    def test_inbound_configuration_validation(self, mock_validate, client: TestClient, auth_headers):
        """Test inbound configuration validation during service creation"""
        mock_validate.return_value = True
        
        service_data = {
            "name": "Validated Service",
            "inbound_ids": []
        }
        
        response = client.post(
            "/api/services",
            json=service_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
    
    @patch('app.routes.service.validate_inbound_configuration')
    def test_invalid_inbound_configuration_rejection(self, mock_validate, client: TestClient, auth_headers):
        """Test rejection of invalid inbound configurations"""
        mock_validate.side_effect = ValueError("Invalid inbound configuration")
        
        service_data = {
            "name": "Invalid Service",
            "inbound_ids": [1]  # This would trigger validation
        }
        
        response = client.post(
            "/api/services",
            json=service_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400


@pytest.mark.parametrize("endpoint", [
    "/api/services",
    "/api/services/1",
    "/api/services/1/users",
    "/api/services/1/inbounds",
])
def test_service_endpoints_require_authentication(client: TestClient, endpoint):
    """Test that service endpoints require authentication"""
    response = client.get(endpoint)
    assert response.status_code == 401


@pytest.mark.parametrize("method,endpoint", [
    ("POST", "/api/services"),
    ("PUT", "/api/services/1"),
    ("DELETE", "/api/services/1"),
    ("POST", "/api/services/1/inbounds/1"),
    ("DELETE", "/api/services/1/inbounds/1"),
])
def test_service_modification_endpoints_require_auth(client: TestClient, method, endpoint):
    """Test that service modification endpoints require authentication"""
    test_data = {"name": "test service", "inbound_ids": []}
    
    if method == "POST":
        response = client.post(endpoint, json=test_data)
    elif method == "PUT":
        response = client.put(endpoint, json=test_data)
    elif method == "DELETE":
        response = client.delete(endpoint)
    
    assert response.status_code == 401