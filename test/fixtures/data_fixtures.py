"""
Data fixtures for testing WildOS VPN components
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, List


@pytest.fixture
def sample_user_data() -> Dict:
    """Sample user data for testing"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "data_limit": 10737418240,  # 10GB
        "data_usage": 1073741824,   # 1GB
        "expire": datetime.utcnow() + timedelta(days=30),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_admin_data() -> Dict:
    """Sample admin data for testing"""
    return {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "is_sudo": True,
        "telegram_id": "123456789",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_node_data() -> Dict:
    """Sample node data for testing"""
    return {
        "id": 1,
        "name": "test-node",
        "address": "127.0.0.1",
        "port": 8080,
        "api_port": 8081,
        "certificate": "test-cert",
        "add_as_new_host": True,
        "status": "Connected",
        "last_status_change": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_service_data() -> Dict:
    """Sample service data for testing"""
    return {
        "id": 1,
        "name": "test-service",
        "inbounds": ["vmess", "vless"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_proxy_data() -> Dict:
    """Sample proxy configuration for testing"""
    return {
        "id": 1,
        "type": "vmess",
        "settings": {
            "port": 443,
            "protocol": "vmess",
            "security": "tls"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_system_data() -> Dict:
    """Sample system data for testing"""
    return {
        "cpu_usage": 45.2,
        "memory_usage": 2048,
        "memory_total": 8192,
        "disk_usage": 50.0,
        "disk_total": 100.0,
        "uptime": 3600,
        "load_average": [0.5, 0.7, 0.9]
    }


@pytest.fixture
def sample_notification_data() -> Dict:
    """Sample notification data for testing"""
    return {
        "id": 1,
        "type": "telegram",
        "title": "Test Notification",
        "message": "This is a test notification",
        "data": {"chat_id": "123456789"},
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_subscription_data() -> Dict:
    """Sample subscription data for testing"""
    return {
        "user_id": 1,
        "config_format": "subscription",
        "url": "https://test.example.com/sub/testuser",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_usage_stats() -> List[Dict]:
    """Sample usage statistics for testing"""
    return [
        {
            "user_id": 1,
            "node_id": 1,
            "used_traffic": 1073741824,  # 1GB
            "created_at": datetime.utcnow() - timedelta(hours=1)
        },
        {
            "user_id": 1,
            "node_id": 1,
            "used_traffic": 536870912,   # 512MB
            "created_at": datetime.utcnow()
        }
    ]


@pytest.fixture
def sample_jwt_payload() -> Dict:
    """Sample JWT payload for testing"""
    return {
        "sub": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "is_sudo": True
    }


@pytest.fixture
def sample_grpc_config() -> Dict:
    """Sample gRPC configuration for testing"""
    return {
        "host": "127.0.0.1",
        "port": 8080,
        "certificate": "test-certificate",
        "timeout": 30,
        "retry_attempts": 3
    }


@pytest.fixture
def sample_xray_config() -> Dict:
    """Sample Xray configuration for testing"""
    return {
        "log": {
            "access": "/var/log/xray/access.log",
            "error": "/var/log/xray/error.log",
            "loglevel": "warning"
        },
        "inbounds": [
            {
                "port": 443,
                "protocol": "vmess",
                "settings": {
                    "clients": []
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "tls"
                }
            }
        ],
        "outbounds": [
            {
                "protocol": "freedom",
                "settings": {}
            }
        ]
    }