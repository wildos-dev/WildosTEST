"""
Comprehensive unit tests for WildosNode VPN backends.

Tests all VPN backends: XrayBackend, SingBoxBackend, HysteriaBackend
- Backend initialization and configuration
- User management (add/remove users)
- Backend operations (start/stop/restart) 
- Stats and logging
- Error handling and edge cases
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path

from wildosnode.backends.abstract_backend import VPNBackend
from wildosnode.backends.xray.xray_backend import XrayBackend
from wildosnode.backends.singbox.singbox_backend import SingBoxBackend
from wildosnode.backends.hysteria2.hysteria2_backend import HysteriaBackend
from wildosnode.models import User, Inbound
from wildosnode.storage.memory import MemoryStorage


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(id=1, username="testuser", key="test-key-123")


@pytest.fixture
def sample_inbound():
    """Sample inbound for testing"""
    return Inbound(tag="test-inbound", protocol="vmess", config={"port": 443})


@pytest.fixture
def mock_storage():
    """Mock storage for testing"""
    storage = MemoryStorage()
    return storage


@pytest.fixture
def xray_config():
    """Sample Xray configuration"""
    return {
        "log": {"level": "warning"},
        "api": {"tag": "api", "services": ["HandlerService", "LoggerService", "StatsService"]},
        "stats": {},
        "policy": {"levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}}},
        "inbounds": [
            {
                "tag": "vmess-in",
                "port": 443,
                "protocol": "vmess",
                "settings": {"clients": []},
                "streamSettings": {"network": "tcp"}
            }
        ],
        "outbounds": [
            {
                "tag": "direct",
                "protocol": "freedom",
                "settings": {}
            }
        ],
        "routing": {"rules": []}
    }


@pytest.fixture
def singbox_config():
    """Sample SingBox configuration"""
    return {
        "log": {"level": "warn"},
        "inbounds": [
            {
                "tag": "vmess-in",
                "type": "vmess",
                "listen": "::",
                "listen_port": 443,
                "users": []
            }
        ],
        "outbounds": [
            {
                "tag": "direct",
                "type": "direct"
            }
        ]
    }


@pytest.fixture
def hysteria2_config():
    """Sample Hysteria2 configuration"""
    return """
listen: :443
tls:
  cert: /path/to/cert.pem
  key: /path/to/key.pem
auth:
  type: http
  http:
    url: http://127.0.0.1:8080/
    timeout: 10s
"""


class TestAbstractVPNBackend:
    """Test abstract VPN backend interface"""
    
    def test_abstract_backend_interface(self):
        """Test that VPNBackend defines the correct interface"""
        # Verify abstract methods are defined
        abstract_methods = [
            'version', 'running', 'contains_tag', 'start', 'restart',
            'add_user', 'remove_user', 'get_logs', 'get_usages',
            'list_inbounds', 'get_config'
        ]
        
        for method in abstract_methods:
            assert hasattr(VPNBackend, method)
            
    def test_backend_type_attributes(self):
        """Test that backend type attributes exist"""
        assert hasattr(VPNBackend, 'backend_type')
        assert hasattr(VPNBackend, 'config_format')


class TestXrayBackend:
    """Test XrayBackend implementation"""
    
    @pytest.fixture
    def xray_backend(self, mock_storage):
        """Create XrayBackend instance for testing"""
        with patch('wildosnode.backends.xray.xray_backend.XrayCore') as mock_core:
            mock_runner = MagicMock()
            mock_runner.running = True
            mock_runner.version = "1.8.0"
            mock_core.return_value = mock_runner
            
            backend = XrayBackend(
                executable_path="/usr/bin/xray",
                assets_path="/usr/share/xray", 
                config_path="/etc/xray/config.json",
                storage=mock_storage
            )
            backend._runner = mock_runner
            return backend
            
    def test_xray_backend_initialization(self, xray_backend):
        """Test XrayBackend initialization"""
        assert xray_backend.backend_type == "xray"
        assert xray_backend.config_format == 1
        assert xray_backend._config_path == "/etc/xray/config.json"
        assert xray_backend._inbound_tags == set()
        assert xray_backend._inbounds == []
        
    def test_xray_running_property(self, xray_backend):
        """Test XrayBackend running property"""
        xray_backend._runner.running = True
        assert xray_backend.running is True
        
        xray_backend._runner.running = False
        assert xray_backend.running is False
        
    def test_xray_version_property(self, xray_backend):
        """Test XrayBackend version property"""
        xray_backend._runner.version = "1.8.0"
        assert xray_backend.version == "1.8.0"
        
    def test_xray_contains_tag(self, xray_backend):
        """Test XrayBackend contains_tag method"""
        xray_backend._inbound_tags = {"vmess-in", "vless-in"}
        
        assert xray_backend.contains_tag("vmess-in") is True
        assert xray_backend.contains_tag("vless-in") is True
        assert xray_backend.contains_tag("non-existent") is False
        
    def test_xray_list_inbounds(self, xray_backend, sample_inbound):
        """Test XrayBackend list_inbounds method"""
        xray_backend._inbounds = [sample_inbound]
        inbounds = xray_backend.list_inbounds()
        
        assert len(inbounds) == 1
        assert inbounds[0] == sample_inbound
        
    def test_xray_get_config(self, xray_backend, xray_config):
        """Test XrayBackend get_config method"""
        config_json = json.dumps(xray_config)
        
        with patch('builtins.open', mock_open(read_data=config_json)):
            config = xray_backend.get_config()
            assert config == config_json
            
    def test_xray_save_config(self, xray_backend, xray_config):
        """Test XrayBackend save_config method"""
        config_json = json.dumps(xray_config, indent=2)
        
        with patch('builtins.open', mock_open()) as mock_file:
            xray_backend.save_config(config_json)
            mock_file.assert_called_once_with("/etc/xray/config.json", "w")
            mock_file().write.assert_called_once_with(config_json)
            
    @pytest.mark.asyncio
    async def test_xray_start(self, xray_backend, xray_config, mock_storage):
        """Test XrayBackend start method"""
        config_json = json.dumps(xray_config)
        
        with patch('builtins.open', mock_open(read_data=config_json)), \
             patch('wildosnode.backends.xray.xray_backend.find_free_port', return_value=10085), \
             patch('wildosnode.backends.xray.xray_backend.XrayConfig') as mock_config, \
             patch('wildosnode.backends.xray.xray_backend.XrayAPI') as mock_api:
            
            # Setup mock config
            mock_config_instance = MagicMock()
            mock_config_instance.inbounds = [{"tag": "vmess-in"}]
            mock_config_instance.list_inbounds.return_value = [
                Inbound(tag="vmess-in", protocol="vmess", config={})
            ]
            mock_config.return_value = mock_config_instance
            
            # Setup mock runner
            xray_backend._runner.start = AsyncMock()
            
            await xray_backend.start()
            
            # Verify configuration setup
            mock_config.assert_called_once()
            mock_config_instance.register_inbounds.assert_called_once_with(mock_storage)
            assert xray_backend._inbound_tags == {"vmess-in"}
            xray_backend._runner.start.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_xray_restart(self, xray_backend, xray_config):
        """Test XrayBackend restart method"""
        config_json = json.dumps(xray_config)
        
        # Mock restart lock
        xray_backend._restart_lock = AsyncMock()
        xray_backend._restart_lock.acquire = AsyncMock()
        xray_backend._restart_lock.release = MagicMock()
        
        xray_backend.stop = AsyncMock()
        xray_backend.start = AsyncMock()
        
        await xray_backend.restart(config_json)
        
        # Verify restart process
        xray_backend._restart_lock.acquire.assert_called_once()
        xray_backend.stop.assert_called_once()
        xray_backend.start.assert_called_once_with(config_json)
        
    @pytest.mark.asyncio
    async def test_xray_add_user(self, xray_backend, sample_user, sample_inbound):
        """Test XrayBackend add_user method"""
        # Setup mock API
        xray_backend._api = AsyncMock()
        xray_backend._api.add_inbound_user = AsyncMock()
        
        with patch('wildosnode.backends.xray.api.types.account.accounts_map') as mock_accounts:
            mock_account_class = MagicMock()
            mock_account_instance = MagicMock()
            mock_account_class.return_value = mock_account_instance
            mock_accounts = {"vmess": mock_account_class}
            
            sample_inbound.config["flow"] = ""
            
            await xray_backend.add_user(sample_user, sample_inbound)
            
            # Verify user addition
            xray_backend._api.add_inbound_user.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_xray_remove_user(self, xray_backend, sample_user, sample_inbound):
        """Test XrayBackend remove_user method"""
        xray_backend._api = AsyncMock()
        xray_backend._api.remove_inbound_user = AsyncMock()
        
        await xray_backend.remove_user(sample_user, sample_inbound)
        
        # Verify user removal
        expected_email = f"{sample_user.id}.{sample_user.username}"
        xray_backend._api.remove_inbound_user.assert_called_once_with(
            sample_inbound.tag, expected_email
        )
        
    @pytest.mark.asyncio
    async def test_xray_get_usages(self, xray_backend):
        """Test XrayBackend get_usages method"""
        # Setup mock API with stats
        mock_stat1 = MagicMock()
        mock_stat1.name = "1.testuser1"
        mock_stat1.value = 1024000
        
        mock_stat2 = MagicMock()
        mock_stat2.name = "2.testuser2"
        mock_stat2.value = 2048000
        
        xray_backend._api = AsyncMock()
        xray_backend._api.get_users_stats = AsyncMock(return_value=[mock_stat1, mock_stat2])
        
        usage_stats = await xray_backend.get_usages()
        
        # Verify usage statistics
        assert usage_stats[1] == 1024000
        assert usage_stats[2] == 2048000
        
    @pytest.mark.asyncio 
    async def test_xray_get_logs(self, xray_backend):
        """Test XrayBackend get_logs method"""
        # Setup mock runner
        xray_backend._runner.get_buffer.return_value = ["Buffer log 1", "Buffer log 2"]
        
        mock_log_stream = AsyncMock()
        async def mock_log_lines():
            yield "Stream log 1"
            yield "Stream log 2"
        mock_log_stream.__aenter__ = AsyncMock(return_value=mock_log_stream)
        mock_log_stream.__aexit__ = AsyncMock(return_value=None)
        mock_log_stream.__aiter__ = lambda self: mock_log_lines()
        
        xray_backend._runner.get_logs_stm.return_value = mock_log_stream
        
        logs = []
        async for log_line in xray_backend.get_logs(include_buffer=True):
            logs.append(log_line)
            
        # Verify logs include both buffer and stream
        assert "Buffer log 1" in logs
        assert "Buffer log 2" in logs
        assert "Stream log 1" in logs
        assert "Stream log 2" in logs


class TestSingBoxBackend:
    """Test SingBoxBackend implementation"""
    
    @pytest.fixture
    def singbox_backend(self, mock_storage):
        """Create SingBoxBackend instance for testing"""
        with patch('wildosnode.backends.singbox.singbox_backend.SingBoxRunner') as mock_runner:
            mock_runner_instance = MagicMock()
            mock_runner_instance.running = True
            mock_runner_instance.version = "1.5.0"
            mock_runner.return_value = mock_runner_instance
            
            backend = SingBoxBackend(
                executable_path="/usr/bin/sing-box",
                config_path="/etc/sing-box/config.json",
                storage=mock_storage
            )
            backend._runner = mock_runner_instance
            return backend
            
    def test_singbox_backend_initialization(self, singbox_backend):
        """Test SingBoxBackend initialization"""
        assert singbox_backend.backend_type == "sing-box"
        assert singbox_backend.config_format == 1
        assert singbox_backend._config_path == "/etc/sing-box/config.json"
        assert singbox_backend._full_config_path == "/etc/sing-box/config.json.full"
        
    @pytest.mark.asyncio
    async def test_singbox_start(self, singbox_backend, singbox_config):
        """Test SingBoxBackend start method"""
        config_json = json.dumps(singbox_config)
        
        with patch('builtins.open', mock_open(read_data=config_json)), \
             patch('wildosnode.backends.singbox.singbox_backend.find_free_port', return_value=8080), \
             patch('wildosnode.backends.singbox.singbox_backend.SingBoxConfig') as mock_config, \
             patch('wildosnode.backends.singbox.singbox_backend.SingBoxAPI') as mock_api:
            
            # Setup mock config
            mock_config_instance = MagicMock()
            mock_config_instance.inbounds = [{"tag": "vmess-in"}]
            mock_config_instance.list_inbounds.return_value = [
                Inbound(tag="vmess-in", protocol="vmess", config={})
            ]
            mock_config_instance.to_json.return_value = config_json
            mock_config.return_value = mock_config_instance
            
            singbox_backend._runner.start = AsyncMock()
            singbox_backend.add_storage_users = AsyncMock()
            
            await singbox_backend.start()
            
            # Verify initialization
            assert singbox_backend._inbound_tags == {"vmess-in"}
            singbox_backend._runner.start.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_singbox_add_user(self, singbox_backend, sample_user, sample_inbound):
        """Test SingBoxBackend add_user method"""
        # Setup mock config
        singbox_backend._config = MagicMock()
        singbox_backend._config.append_user = MagicMock()
        singbox_backend._config_update_event = MagicMock()
        singbox_backend._config_update_event.set = MagicMock()
        
        # Mock config modification lock
        singbox_backend._config_modification_lock = AsyncMock()
        singbox_backend._config_modification_lock.__aenter__ = AsyncMock()
        singbox_backend._config_modification_lock.__aexit__ = AsyncMock()
        
        await singbox_backend.add_user(sample_user, sample_inbound)
        
        # Verify user addition
        singbox_backend._config.append_user.assert_called_once_with(sample_user, sample_inbound)
        singbox_backend._config_update_event.set.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_singbox_remove_user(self, singbox_backend, sample_user, sample_inbound):
        """Test SingBoxBackend remove_user method"""
        # Setup mock config
        singbox_backend._config = MagicMock()
        singbox_backend._config.pop_user = MagicMock()
        singbox_backend._config_update_event = MagicMock()
        singbox_backend._config_update_event.set = MagicMock()
        
        # Mock config modification lock
        singbox_backend._config_modification_lock = AsyncMock()
        singbox_backend._config_modification_lock.__aenter__ = AsyncMock()
        singbox_backend._config_modification_lock.__aexit__ = AsyncMock()
        
        await singbox_backend.remove_user(sample_user, sample_inbound)
        
        # Verify user removal
        singbox_backend._config.pop_user.assert_called_once_with(sample_user, sample_inbound)
        singbox_backend._config_update_event.set.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_singbox_get_usages(self, singbox_backend):
        """Test SingBoxBackend get_usages method"""
        # Setup mock API
        mock_stat1 = MagicMock()
        mock_stat1.name = "1.testuser1"
        mock_stat1.value = 1024000
        
        singbox_backend._api = AsyncMock()
        singbox_backend._api.get_users_stats = AsyncMock(return_value=[mock_stat1])
        
        with patch('asyncio.wait_for', side_effect=lambda coro, timeout: coro):
            usage_stats = await singbox_backend.get_usages()
            
        # Verify usage statistics
        assert usage_stats[1] == 1024000


class TestHysteriaBackend:
    """Test HysteriaBackend implementation"""
    
    @pytest.fixture
    def hysteria_backend(self, mock_storage):
        """Create HysteriaBackend instance for testing"""
        with patch('wildosnode.backends.hysteria2.hysteria2_backend.Hysteria') as mock_hysteria:
            mock_hysteria_instance = MagicMock()
            mock_hysteria_instance.running = True
            mock_hysteria_instance.version = "2.0.0"
            mock_hysteria.return_value = mock_hysteria_instance
            
            backend = HysteriaBackend(
                executable_path="/usr/bin/hysteria",
                config_path="/etc/hysteria/config.yaml",
                storage=mock_storage
            )
            backend._runner = mock_hysteria_instance
            return backend
            
    def test_hysteria_backend_initialization(self, hysteria_backend):
        """Test HysteriaBackend initialization"""
        assert hysteria_backend.backend_type == "hysteria2"
        assert hysteria_backend.config_format == 2  # YAML format
        assert hysteria_backend._config_path == "/etc/hysteria/config.yaml"
        assert hysteria_backend._inbound_tags == ["hysteria2"]
        
    def test_hysteria_contains_tag(self, hysteria_backend):
        """Test HysteriaBackend contains_tag method"""
        assert hysteria_backend.contains_tag("hysteria2") is True
        assert hysteria_backend.contains_tag("other-tag") is False
        
    @pytest.mark.asyncio
    async def test_hysteria_start(self, hysteria_backend, hysteria2_config):
        """Test HysteriaBackend start method"""
        with patch('builtins.open', mock_open(read_data=hysteria2_config)), \
             patch('wildosnode.backends.hysteria2.hysteria2_backend.find_free_port', side_effect=[8080, 9090]), \
             patch('secrets.token_hex', return_value='test-secret'), \
             patch('wildosnode.backends.hysteria2.hysteria2_backend.HysteriaConfig') as mock_config, \
             patch('aiohttp.web.Application') as mock_app, \
             patch('aiohttp.web.AppRunner') as mock_runner, \
             patch('aiohttp.web.TCPSite') as mock_site:
            
            # Setup mock config
            mock_config_instance = MagicMock()
            mock_config_instance.get_inbound.return_value = Inbound(
                tag="hysteria2", protocol="hysteria2", config={}
            )
            mock_config_instance.render.return_value = hysteria2_config
            mock_config.return_value = mock_config_instance
            
            # Setup mock web components
            mock_runner_instance = AsyncMock()
            mock_runner.return_value = mock_runner_instance
            mock_site_instance = AsyncMock()
            mock_site.return_value = mock_site_instance
            
            hysteria_backend._runner.start = AsyncMock()
            
            await hysteria_backend.start()
            
            # Verify web app setup
            mock_runner_instance.setup.assert_called_once()
            mock_site_instance.start.assert_called_once()
            hysteria_backend._runner.start.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_hysteria_add_user(self, hysteria_backend, sample_user, sample_inbound):
        """Test HysteriaBackend add_user method"""
        with patch('wildosnode.backends.hysteria2.hysteria2_backend.generate_password', return_value='test-password'):
            await hysteria_backend.add_user(sample_user, sample_inbound)
            
            # Verify user was added to internal storage
            assert 'test-password' in hysteria_backend._users
            assert hysteria_backend._users['test-password'] == sample_user
            
    @pytest.mark.asyncio
    async def test_hysteria_remove_user(self, hysteria_backend, sample_user, sample_inbound):
        """Test HysteriaBackend remove_user method"""
        # Add user first
        test_password = 'test-password'
        hysteria_backend._users[test_password] = sample_user
        hysteria_backend._stats_port = 9090
        hysteria_backend._stats_secret = 'test-secret'
        
        with patch('wildosnode.backends.hysteria2.hysteria2_backend.generate_password', return_value=test_password), \
             patch('aiohttp.ClientSession') as mock_session:
            
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.post.return_value.__aenter__.return_value = AsyncMock()
            
            await hysteria_backend.remove_user(sample_user, sample_inbound)
            
            # Verify user was removed and kick request was made
            assert test_password not in hysteria_backend._users
            mock_session_instance.post.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_hysteria_get_usages(self, hysteria_backend):
        """Test HysteriaBackend get_usages method"""
        hysteria_backend._stats_port = 9090
        hysteria_backend._stats_secret = 'test-secret'
        
        mock_response_data = {
            "1.testuser1": {"tx": 500000, "rx": 500000},
            "2.testuser2": {"tx": 1000000, "rx": 1000000}
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.get.return_value.__aenter__.return_value = mock_response
            
            usage_stats = await hysteria_backend.get_usages()
            
            # Verify usage calculations
            assert usage_stats[1] == 1000000  # tx + rx
            assert usage_stats[2] == 2000000  # tx + rx
            
    @pytest.mark.asyncio
    async def test_hysteria_auth_callback_valid_user(self, hysteria_backend, sample_user):
        """Test HysteriaBackend auth callback with valid user"""
        # Setup user in backend
        test_key = 'valid-auth-key'
        hysteria_backend._users[test_key] = sample_user
        
        # Create mock request
        mock_request = AsyncMock()
        mock_request.json.return_value = {"auth": test_key}
        
        response = await hysteria_backend._auth_callback(mock_request)
        
        # Verify successful authentication
        expected_body = json.dumps({"ok": True, "id": f"{sample_user.id}.{sample_user.username}"})
        assert response.body == expected_body
        
    @pytest.mark.asyncio
    async def test_hysteria_auth_callback_invalid_user(self, hysteria_backend):
        """Test HysteriaBackend auth callback with invalid user"""
        # Create mock request with invalid key
        mock_request = AsyncMock()
        mock_request.json.return_value = {"auth": "invalid-key"}
        
        with patch('aiohttp.web.Response') as mock_response:
            response = await hysteria_backend._auth_callback(mock_request)
            
            # Verify authentication failure
            mock_response.assert_called_with(status=404)


class TestBackendErrorHandling:
    """Test error handling in all backends"""
    
    @pytest.mark.asyncio
    async def test_xray_backend_api_errors(self, mock_storage):
        """Test XrayBackend handling of API errors"""
        from wildosnode.backends.xray.api.exceptions import EmailExistsError
        
        with patch('wildosnode.backends.xray.xray_backend.XrayCore'):
            backend = XrayBackend("/usr/bin/xray", "/usr/share/xray", "/etc/xray/config.json", mock_storage)
            backend._api = AsyncMock()
            backend._api.add_inbound_user.side_effect = EmailExistsError("Email exists")
            
            sample_user = User(id=1, username="test", key="key")
            sample_inbound = Inbound(tag="test", protocol="vmess", config={"flow": ""})
            
            with patch('wildosnode.backends.xray.api.types.account.accounts_map', {"vmess": MagicMock()}):
                with pytest.raises(EmailExistsError):
                    await backend.add_user(sample_user, sample_inbound)
                    
    @pytest.mark.asyncio
    async def test_singbox_backend_api_timeout(self, mock_storage):
        """Test SingBoxBackend handling of API timeouts"""
        with patch('wildosnode.backends.singbox.singbox_backend.SingBoxRunner'):
            backend = SingBoxBackend("/usr/bin/sing-box", "/etc/sing-box/config.json", mock_storage)
            backend._api = AsyncMock()
            
            # Simulate timeout
            with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                usage_stats = await backend.get_usages()
                # Should return empty stats on timeout
                assert usage_stats == {}
                
    @pytest.mark.asyncio
    async def test_hysteria_backend_connection_error(self, mock_storage):
        """Test HysteriaBackend handling of connection errors"""
        from aiohttp import ClientConnectorError
        
        with patch('wildosnode.backends.hysteria2.hysteria2_backend.Hysteria'):
            backend = HysteriaBackend("/usr/bin/hysteria", "/etc/hysteria/config.yaml", mock_storage)
            backend._stats_port = 9090
            backend._stats_secret = 'test-secret'
            
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session_instance = AsyncMock()
                mock_session_instance.get.side_effect = ClientConnectorError(MagicMock(), OSError("Connection failed"))
                mock_session.return_value.__aenter__.return_value = mock_session_instance
                
                usage_stats = await backend.get_usages()
                # Should return empty dict on connection error
                assert usage_stats == {}


class TestBackendIntegration:
    """Test integration scenarios between backends and storage"""
    
    @pytest.mark.asyncio
    async def test_backend_storage_integration(self, mock_storage):
        """Test backend integration with storage"""
        # Add test data to storage
        test_user = User(id=1, username="testuser", key="testkey")
        test_inbound = Inbound(tag="test-inbound", protocol="vmess", config={})
        
        mock_storage.register_inbound(test_inbound)
        await mock_storage.update_user_inbounds(test_user, [test_inbound])
        
        # Test storage queries
        users = await mock_storage.list_users()
        assert len(users) == 1
        assert users[0].username == "testuser"
        
        inbound_users = await mock_storage.list_inbound_users("test-inbound")
        assert len(inbound_users) == 1
        assert inbound_users[0].id == 1
        
    @pytest.mark.asyncio
    async def test_multiple_backends_coordination(self, mock_storage):
        """Test coordination between multiple backends"""
        with patch('wildosnode.backends.xray.xray_backend.XrayCore'), \
             patch('wildosnode.backends.singbox.singbox_backend.SingBoxRunner'):
            
            xray_backend = XrayBackend("/usr/bin/xray", "/usr/share/xray", "/etc/xray/config.json", mock_storage)
            singbox_backend = SingBoxBackend("/usr/bin/sing-box", "/etc/sing-box/config.json", mock_storage)
            
            # Test tag isolation
            xray_backend._inbound_tags = {"xray-vmess"}
            singbox_backend._inbound_tags = {"singbox-vmess"}
            
            assert xray_backend.contains_tag("xray-vmess") is True
            assert xray_backend.contains_tag("singbox-vmess") is False
            
            assert singbox_backend.contains_tag("singbox-vmess") is True
            assert singbox_backend.contains_tag("xray-vmess") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])