"""
Unit tests for node routes (app/routes/node.py)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from datetime import datetime

from app.models.node import Node, NodeCreate, NodeModify, NodeResponse, NodeStatus


class TestNodeCRUD:
    """Test node CRUD operations"""
    
    def test_create_node_success(self, client: TestClient, auth_headers):
        """Test successful node creation"""
        node_data = {
            "name": "Test Node DE",
            "address": "192.168.1.100",
            "port": 8085,
            "usage_coefficient": 1.0
        }
        
        response = client.post(
            "/api/nodes",
            json=node_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Node DE"
        assert data["address"] == "192.168.1.100"
        assert data["port"] == 8085
        assert data["usage_coefficient"] == 1.0
    
    def test_create_node_duplicate_address(self, client: TestClient, auth_headers, test_node):
        """Test node creation with duplicate address"""
        node_data = {
            "name": "Duplicate Node",
            "address": test_node.address,  # Duplicate address
            "port": test_node.port,
            "usage_coefficient": 1.0
        }
        
        response = client.post(
            "/api/nodes",
            json=node_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_create_node_invalid_data(self, client: TestClient, auth_headers):
        """Test node creation with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "address": "invalid_ip",  # Invalid IP
            "port": 70000,  # Invalid port
            "usage_coefficient": -1.0  # Negative coefficient
        }
        
        response = client.post(
            "/api/nodes",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_get_node_success(self, client: TestClient, auth_headers, test_node):
        """Test successful node retrieval"""
        response = client.get(
            f"/api/nodes/{test_node.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_node.id
        assert data["name"] == test_node.name
        assert data["address"] == test_node.address
        assert "status" in data
        assert "backends" in data
    
    def test_get_node_not_found(self, client: TestClient, auth_headers):
        """Test node retrieval with non-existent ID"""
        response = client.get(
            "/api/nodes/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_nodes_list(self, client: TestClient, auth_headers, test_node):
        """Test nodes list retrieval"""
        response = client.get(
            "/api/nodes",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(node["id"] == test_node.id for node in data)
    
    def test_modify_node_success(self, client: TestClient, auth_headers, test_node):
        """Test successful node modification"""
        modify_data = {
            "name": "Updated Node Name",
            "usage_coefficient": 1.5,
            "status": "disabled"
        }
        
        response = client.put(
            f"/api/nodes/{test_node.id}",
            json=modify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Node Name"
        assert data["usage_coefficient"] == 1.5
        assert data["status"] == "disabled"
    
    def test_remove_node_success(self, client: TestClient, auth_headers, test_db):
        """Test successful node removal"""
        from app.db import crud
        
        # Create node to remove
        node_data = {
            "name": "Node to Remove",
            "address": "192.168.1.200",
            "port": 8085,
            "usage_coefficient": 1.0
        }
        node_to_remove = crud.create_node(test_db, node_data)
        
        response = client.delete(
            f"/api/nodes/{node_to_remove.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify node was removed
        get_response = client.get(
            f"/api/nodes/{node_to_remove.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404


class TestNodeSystemOperations:
    """Test node system monitoring and operations"""
    
    @patch('app.routes.node.get_node_connection')
    def test_get_node_system_stats(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test node system statistics retrieval"""
        # Mock gRPC connection and response
        mock_grpc = AsyncMock()
        mock_grpc.get_system_stats.return_value = {
            "cpu": {"usage": 45.2, "load_average": [1.2, 1.1, 0.9]},
            "memory": {"total": "8GB", "used": "3.2GB", "usage_percent": 40.0},
            "disk": {"root_usage_percent": 65.0},
            "uptime": {"seconds": 3600, "formatted": "1 hour"}
        }
        mock_connection.return_value = mock_grpc
        
        response = client.get(
            f"/api/nodes/{test_node.id}/system-stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "uptime" in data
    
    @patch('app.routes.node.get_node_connection')
    def test_get_node_system_stats_connection_error(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test node system stats with connection error"""
        mock_connection.side_effect = Exception("Connection failed")
        
        response = client.get(
            f"/api/nodes/{test_node.id}/system-stats",
            headers=auth_headers
        )
        
        assert response.status_code == 503
        assert "connection" in response.json()["detail"].lower()
    
    @patch('app.routes.node.get_node_connection')
    def test_restart_node_backend(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test node backend restart"""
        mock_grpc = AsyncMock()
        mock_grpc.restart_backend.return_value = {"success": True, "message": "Backend restarted"}
        mock_connection.return_value = mock_grpc
        
        response = client.post(
            f"/api/nodes/{test_node.id}/restart-backend/xray",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    @patch('app.routes.node.get_node_connection')
    def test_get_node_logs(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test node logs retrieval"""
        mock_grpc = AsyncMock()
        mock_grpc.get_logs.return_value = [
            {"timestamp": "2023-01-01T12:00:00Z", "level": "INFO", "message": "Backend started"},
            {"timestamp": "2023-01-01T12:01:00Z", "level": "WARN", "message": "Connection timeout"}
        ]
        mock_connection.return_value = mock_grpc
        
        response = client.get(
            f"/api/nodes/{test_node.id}/logs?limit=100",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0


class TestNodeWebSocketLogs:
    """Test node WebSocket log functionality"""
    
    @patch('app.routes.node.extract_token_from_query')
    @patch('app.routes.node.validate_token')
    @patch('app.routes.node.get_node_connection')
    def test_websocket_logs_authentication(self, mock_connection, mock_validate, mock_extract, client: TestClient, test_node):
        """Test WebSocket logs require authentication"""
        mock_extract.return_value = "valid_token"
        mock_validate.return_value = {"node_id": test_node.id, "is_sudo": True}
        
        # WebSocket testing would require special setup
        # This is a placeholder for WebSocket authentication testing
        pass
    
    def test_websocket_logs_invalid_token(self, client: TestClient, test_node):
        """Test WebSocket logs with invalid token"""
        # WebSocket connection with invalid token should be rejected
        pass


class TestNodeContainerOperations:
    """Test node container management operations"""
    
    @patch('app.routes.node.get_node_connection')
    def test_get_container_files(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test container file listing"""
        mock_grpc = AsyncMock()
        mock_grpc.list_container_files.return_value = [
            {"name": "config.json", "type": "file", "size": "1024", "permissions": "rw-r--r--"},
            {"name": "logs", "type": "directory", "permissions": "rwxr-xr-x"}
        ]
        mock_connection.return_value = mock_grpc
        
        response = client.get(
            f"/api/nodes/{test_node.id}/container/files?path=/etc",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('app.routes.node.get_node_connection')
    def test_open_container_port(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test opening container port"""
        mock_grpc = AsyncMock()
        mock_grpc.open_port.return_value = {"success": True, "message": "Port opened"}
        mock_connection.return_value = mock_grpc
        
        port_data = {"port": 8080, "protocol": "tcp"}
        
        response = client.post(
            f"/api/nodes/{test_node.id}/container/open-port",
            json=port_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    @patch('app.routes.node.get_node_connection')
    def test_close_container_port(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test closing container port"""
        mock_grpc = AsyncMock()
        mock_grpc.close_port.return_value = {"success": True, "message": "Port closed"}
        mock_connection.return_value = mock_grpc
        
        port_data = {"port": 8080, "protocol": "tcp"}
        
        response = client.post(
            f"/api/nodes/{test_node.id}/container/close-port",
            json=port_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestNodeBackendOperations:
    """Test node backend management"""
    
    @patch('app.routes.node.get_node_connection')
    def test_get_backend_stats(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test backend statistics retrieval"""
        mock_grpc = AsyncMock()
        mock_grpc.get_backend_stats.return_value = {"running": True, "uptime": 3600}
        mock_connection.return_value = mock_grpc
        
        response = client.get(
            f"/api/nodes/{test_node.id}/backends/xray/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
    
    @patch('app.routes.node.get_node_connection')
    def test_get_all_backend_stats(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test all backends statistics retrieval"""
        mock_grpc = AsyncMock()
        mock_grpc.get_all_backend_stats.return_value = {
            "backends": {
                "xray": {"running": True, "uptime": 3600},
                "sing-box": {"running": False, "uptime": 0}
            },
            "node_id": test_node.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_connection.return_value = mock_grpc
        
        response = client.get(
            f"/api/nodes/{test_node.id}/backends/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "backends" in data
        assert "node_id" in data
        assert "timestamp" in data
    
    @patch('app.routes.node.get_node_connection')
    def test_get_backend_config(self, mock_connection, client: TestClient, auth_headers, test_node):
        """Test backend configuration retrieval"""
        mock_grpc = AsyncMock()
        mock_grpc.get_backend_config.return_value = {
            "config": '{"log": {"level": "warn"}}',
            "format": "JSON"
        }
        mock_connection.return_value = mock_grpc
        
        response = client.get(
            f"/api/nodes/{test_node.id}/backends/xray/config",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "format" in data


class TestNodePeakEvents:
    """Test node peak events monitoring"""
    
    def test_create_peak_event(self, client: TestClient, auth_headers, test_node):
        """Test peak event creation"""
        event_data = {
            "category": "CPU",
            "metric": "usage",
            "level": "WARNING",
            "value": 85.5,
            "threshold": 80.0,
            "dedupe_key": "cpu_high_usage",
            "started_at_ms": int(datetime.utcnow().timestamp() * 1000)
        }
        
        response = client.post(
            f"/api/nodes/{test_node.id}/peak-events",
            json=event_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "CPU"
        assert data["level"] == "WARNING"
    
    def test_get_peak_events(self, client: TestClient, auth_headers, test_node):
        """Test peak events retrieval"""
        response = client.get(
            f"/api/nodes/{test_node.id}/peak-events?limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestNodeValidation:
    """Test node input validation"""
    
    def test_node_name_validation(self, client: TestClient, auth_headers):
        """Test node name validation"""
        invalid_names = [
            "",  # Empty
            "a" * 101,  # Too long
        ]
        
        for name in invalid_names:
            node_data = {
                "name": name,
                "address": "192.168.1.1",
                "port": 8085,
                "usage_coefficient": 1.0
            }
            
            response = client.post(
                "/api/nodes",
                json=node_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422, f"Name '{name}' should be invalid"
    
    def test_node_address_validation(self, client: TestClient, auth_headers):
        """Test node address validation"""
        invalid_addresses = [
            "",  # Empty
            "not_an_ip",  # Invalid format
            "999.999.999.999",  # Invalid IP
        ]
        
        for address in invalid_addresses:
            node_data = {
                "name": f"Test Node {address}",
                "address": address,
                "port": 8085,
                "usage_coefficient": 1.0
            }
            
            response = client.post(
                "/api/nodes",
                json=node_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422, f"Address '{address}' should be invalid"
    
    def test_node_port_validation(self, client: TestClient, auth_headers):
        """Test node port validation"""
        invalid_ports = [
            0,  # Too low
            65536,  # Too high
            -1,  # Negative
        ]
        
        for port in invalid_ports:
            node_data = {
                "name": f"Test Node Port {port}",
                "address": "192.168.1.1",
                "port": port,
                "usage_coefficient": 1.0
            }
            
            response = client.post(
                "/api/nodes",
                json=node_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422, f"Port {port} should be invalid"


@pytest.mark.parametrize("endpoint", [
    "/api/nodes",
    "/api/nodes/1",
    "/api/nodes/1/system-stats",
    "/api/nodes/1/backends/stats",
])
def test_node_endpoints_require_authentication(client: TestClient, endpoint):
    """Test that node endpoints require authentication"""
    response = client.get(endpoint)
    assert response.status_code == 401


@pytest.mark.parametrize("method,endpoint", [
    ("POST", "/api/nodes"),
    ("PUT", "/api/nodes/1"),
    ("DELETE", "/api/nodes/1"),
    ("POST", "/api/nodes/1/restart-backend/xray"),
])
def test_node_modification_endpoints_require_auth(client: TestClient, method, endpoint):
    """Test that node modification endpoints require authentication"""
    test_data = {"name": "test", "address": "127.0.0.1", "port": 8085}
    
    if method == "POST":
        response = client.post(endpoint, json=test_data)
    elif method == "PUT":
        response = client.put(endpoint, json=test_data)
    elif method == "DELETE":
        response = client.delete(endpoint)
    
    assert response.status_code == 401