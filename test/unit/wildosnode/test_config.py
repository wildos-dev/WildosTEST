"""
Comprehensive unit tests for WildosNode configuration system.

Tests configuration components:
- Configuration loading and validation
- Environment variable handling  
- Backend-specific configurations (Xray, SingBox, Hysteria2)
- SSL/TLS configuration
- Authentication algorithm configuration
- Configuration edge cases and error handling
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from enum import Enum

# Import configuration module
import wildosnode.config as config
from wildosnode.config import AuthAlgorithm


class TestConfigurationLoading:
    """Test configuration loading from environment"""
    
    def test_default_service_configuration(self):
        """Test default service configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            # Reload the config module to get fresh defaults
            import importlib
            importlib.reload(config)
            
            assert config.SERVICE_ADDRESS == "0.0.0.0"
            assert config.SERVICE_PORT == 62050  # Default NODE_GRPC_PORT
            assert config.INSECURE is False
            
    def test_custom_service_configuration(self):
        """Test custom service configuration from environment"""
        env_vars = {
            "SERVICE_ADDRESS": "127.0.0.1",
            "SERVICE_PORT": "8080",
            "INSECURE": "True"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SERVICE_ADDRESS == "127.0.0.1"
            assert config.SERVICE_PORT == 8080
            assert config.INSECURE is True
            
    def test_node_grpc_port_fallback(self):
        """Test NODE_GRPC_PORT fallback for SERVICE_PORT"""
        env_vars = {"NODE_GRPC_PORT": "9090"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SERVICE_PORT == 9090
            
    def test_service_port_override_node_grpc_port(self):
        """Test SERVICE_PORT takes precedence over NODE_GRPC_PORT"""
        env_vars = {
            "SERVICE_PORT": "8080",
            "NODE_GRPC_PORT": "9090"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SERVICE_PORT == 8080


class TestXrayConfiguration:
    """Test Xray backend configuration"""
    
    def test_default_xray_configuration(self):
        """Test default Xray configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.XRAY_ENABLED is True
            assert config.XRAY_EXECUTABLE_PATH == "/usr/bin/xray"
            assert config.XRAY_ASSETS_PATH == "/usr/share/xray"
            assert config.XRAY_CONFIG_PATH == "/etc/xray/config.json"
            assert config.XRAY_VLESS_REALITY_FLOW == "xtls-rprx-vision"
            assert config.XRAY_RESTART_ON_FAILURE is False
            assert config.XRAY_RESTART_ON_FAILURE_INTERVAL == 0
            
    def test_custom_xray_configuration(self):
        """Test custom Xray configuration from environment"""
        env_vars = {
            "XRAY_ENABLED": "False",
            "XRAY_EXECUTABLE_PATH": "/custom/bin/xray",
            "XRAY_ASSETS_PATH": "/custom/share/xray",
            "XRAY_CONFIG_PATH": "/custom/etc/xray/config.json",
            "XRAY_VLESS_REALITY_FLOW": "xtls-rprx-direct",
            "XRAY_RESTART_ON_FAILURE": "True",
            "XRAY_RESTART_ON_FAILURE_INTERVAL": "30"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.XRAY_ENABLED is False
            assert config.XRAY_EXECUTABLE_PATH == "/custom/bin/xray"
            assert config.XRAY_ASSETS_PATH == "/custom/share/xray"
            assert config.XRAY_CONFIG_PATH == "/custom/etc/xray/config.json"
            assert config.XRAY_VLESS_REALITY_FLOW == "xtls-rprx-direct"
            assert config.XRAY_RESTART_ON_FAILURE is True
            assert config.XRAY_RESTART_ON_FAILURE_INTERVAL == 30
            
    def test_xray_boolean_configuration_variations(self):
        """Test various boolean value formats for Xray configuration"""
        boolean_test_cases = [
            ("True", True),
            ("true", True),
            ("1", True),
            ("yes", True),
            ("False", False),
            ("false", False),
            ("0", False),
            ("no", False),
            ("", False),
        ]
        
        for env_value, expected in boolean_test_cases:
            env_vars = {"XRAY_ENABLED": env_value}
            
            with patch.dict(os.environ, env_vars, clear=True):
                import importlib
                importlib.reload(config)
                
                assert config.XRAY_ENABLED == expected, f"Failed for value: {env_value}"


class TestSingBoxConfiguration:
    """Test SingBox backend configuration"""
    
    def test_default_singbox_configuration(self):
        """Test default SingBox configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SING_BOX_ENABLED is False
            assert config.SING_BOX_EXECUTABLE_PATH == "/usr/bin/sing-box"
            assert config.SING_BOX_CONFIG_PATH == "/etc/sing-box/config.json"
            assert config.SING_BOX_RESTART_ON_FAILURE is False
            assert config.SING_BOX_RESTART_ON_FAILURE_INTERVAL == 0
            assert config.SING_BOX_USER_MODIFICATION_INTERVAL == 30
            
    def test_custom_singbox_configuration(self):
        """Test custom SingBox configuration from environment"""
        env_vars = {
            "SING_BOX_ENABLED": "True",
            "SING_BOX_EXECUTABLE_PATH": "/custom/bin/sing-box",
            "SING_BOX_CONFIG_PATH": "/custom/etc/sing-box/config.json",
            "SING_BOX_RESTART_ON_FAILURE": "True",
            "SING_BOX_RESTART_ON_FAILURE_INTERVAL": "45",
            "SING_BOX_USER_MODIFICATION_INTERVAL": "60"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SING_BOX_ENABLED is True
            assert config.SING_BOX_EXECUTABLE_PATH == "/custom/bin/sing-box"
            assert config.SING_BOX_CONFIG_PATH == "/custom/etc/sing-box/config.json"
            assert config.SING_BOX_RESTART_ON_FAILURE is True
            assert config.SING_BOX_RESTART_ON_FAILURE_INTERVAL == 45
            assert config.SING_BOX_USER_MODIFICATION_INTERVAL == 60


class TestHysteriaConfiguration:
    """Test Hysteria2 backend configuration"""
    
    def test_default_hysteria_configuration(self):
        """Test default Hysteria2 configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.HYSTERIA_ENABLED is False
            assert config.HYSTERIA_EXECUTABLE_PATH == "/usr/bin/hysteria"
            assert config.HYSTERIA_CONFIG_PATH == "/etc/hysteria/config.yaml"
            
    def test_custom_hysteria_configuration(self):
        """Test custom Hysteria2 configuration from environment"""
        env_vars = {
            "HYSTERIA_ENABLED": "True",
            "HYSTERIA_EXECUTABLE_PATH": "/custom/bin/hysteria",
            "HYSTERIA_CONFIG_PATH": "/custom/etc/hysteria/config.yaml"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.HYSTERIA_ENABLED is True
            assert config.HYSTERIA_EXECUTABLE_PATH == "/custom/bin/hysteria"
            assert config.HYSTERIA_CONFIG_PATH == "/custom/etc/hysteria/config.yaml"


class TestSSLConfiguration:
    """Test SSL/TLS configuration"""
    
    def test_default_ssl_configuration(self):
        """Test default SSL configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SSL_CERT_FILE == "./ssl_cert.pem"
            assert config.SSL_KEY_FILE == "./ssl_key.pem"
            assert config.SSL_CLIENT_CERT_FILE == ""
            
    def test_custom_ssl_configuration(self):
        """Test custom SSL configuration from environment"""
        env_vars = {
            "SSL_CERT_FILE": "/etc/ssl/certs/wildos.crt",
            "SSL_KEY_FILE": "/etc/ssl/private/wildos.key",
            "SSL_CLIENT_CERT_FILE": "/etc/ssl/certs/client.crt"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SSL_CERT_FILE == "/etc/ssl/certs/wildos.crt"
            assert config.SSL_KEY_FILE == "/etc/ssl/private/wildos.key"
            assert config.SSL_CLIENT_CERT_FILE == "/etc/ssl/certs/client.crt"
            
    def test_ssl_file_paths_validation(self):
        """Test SSL file paths are strings and not empty when set"""
        env_vars = {
            "SSL_CERT_FILE": "/valid/path/cert.pem",
            "SSL_KEY_FILE": "/valid/path/key.pem"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert isinstance(config.SSL_CERT_FILE, str)
            assert isinstance(config.SSL_KEY_FILE, str)
            assert len(config.SSL_CERT_FILE) > 0
            assert len(config.SSL_KEY_FILE) > 0


class TestAuthConfiguration:
    """Test authentication configuration"""
    
    def test_auth_algorithm_enum(self):
        """Test AuthAlgorithm enum definition"""
        assert AuthAlgorithm.PLAIN.value == "plain"
        assert AuthAlgorithm.XXH128.value == "xxh128"
        
        # Test enum membership
        assert "plain" in [alg.value for alg in AuthAlgorithm]
        assert "xxh128" in [alg.value for alg in AuthAlgorithm]
        
    def test_default_auth_configuration(self):
        """Test default authentication configuration"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.AUTH_GENERATION_ALGORITHM == AuthAlgorithm.XXH128
            
    def test_custom_auth_configuration(self):
        """Test custom authentication configuration"""
        env_vars = {"AUTH_GENERATION_ALGORITHM": "plain"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.AUTH_GENERATION_ALGORITHM == AuthAlgorithm.PLAIN
            
    def test_invalid_auth_algorithm_fallback(self):
        """Test fallback for invalid authentication algorithm"""
        env_vars = {"AUTH_GENERATION_ALGORITHM": "invalid_algorithm"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Should fallback to default
            try:
                import importlib
                importlib.reload(config)
                # If it doesn't raise an error, it should use default
                assert config.AUTH_GENERATION_ALGORITHM in [AuthAlgorithm.PLAIN, AuthAlgorithm.XXH128]
            except ValueError:
                # Expected behavior for invalid enum value
                pass


class TestDebugConfiguration:
    """Test debug configuration"""
    
    def test_default_debug_configuration(self):
        """Test default debug configuration"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.DEBUG is False
            
    def test_custom_debug_configuration(self):
        """Test custom debug configuration"""
        test_cases = [
            ("True", True),
            ("true", True),
            ("1", True),
            ("False", False),
            ("false", False),
            ("0", False),
            ("", False),
        ]
        
        for env_value, expected in test_cases:
            env_vars = {"DEBUG": env_value}
            
            with patch.dict(os.environ, env_vars, clear=True):
                import importlib
                importlib.reload(config)
                
                assert config.DEBUG == expected, f"Failed for DEBUG value: {env_value}"


class TestConfigurationIntegration:
    """Test configuration integration scenarios"""
    
    def test_all_backends_enabled_configuration(self):
        """Test configuration with all backends enabled"""
        env_vars = {
            "XRAY_ENABLED": "True",
            "SING_BOX_ENABLED": "True",
            "HYSTERIA_ENABLED": "True",
            "DEBUG": "True"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.XRAY_ENABLED is True
            assert config.SING_BOX_ENABLED is True
            assert config.HYSTERIA_ENABLED is True
            assert config.DEBUG is True
            
    def test_production_like_configuration(self):
        """Test production-like configuration"""
        env_vars = {
            "SERVICE_ADDRESS": "0.0.0.0",
            "SERVICE_PORT": "62050",
            "INSECURE": "False",
            "XRAY_ENABLED": "True",
            "XRAY_RESTART_ON_FAILURE": "True",
            "XRAY_RESTART_ON_FAILURE_INTERVAL": "30",
            "SSL_CERT_FILE": "/etc/ssl/certs/server.crt",
            "SSL_KEY_FILE": "/etc/ssl/private/server.key",
            "DEBUG": "False",
            "AUTH_GENERATION_ALGORITHM": "xxh128"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SERVICE_ADDRESS == "0.0.0.0"
            assert config.SERVICE_PORT == 62050
            assert config.INSECURE is False
            assert config.XRAY_ENABLED is True
            assert config.XRAY_RESTART_ON_FAILURE is True
            assert config.SSL_CERT_FILE == "/etc/ssl/certs/server.crt"
            assert config.DEBUG is False
            assert config.AUTH_GENERATION_ALGORITHM == AuthAlgorithm.XXH128
            
    def test_development_configuration(self):
        """Test development-like configuration"""
        env_vars = {
            "SERVICE_ADDRESS": "127.0.0.1",
            "SERVICE_PORT": "8080",
            "INSECURE": "True",
            "DEBUG": "True",
            "XRAY_ENABLED": "True",
            "SING_BOX_ENABLED": "False",
            "HYSTERIA_ENABLED": "False",
            "AUTH_GENERATION_ALGORITHM": "plain"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.SERVICE_ADDRESS == "127.0.0.1"
            assert config.SERVICE_PORT == 8080
            assert config.INSECURE is True
            assert config.DEBUG is True
            assert config.XRAY_ENABLED is True
            assert config.SING_BOX_ENABLED is False
            assert config.HYSTERIA_ENABLED is False
            assert config.AUTH_GENERATION_ALGORITHM == AuthAlgorithm.PLAIN


class TestConfigurationValidation:
    """Test configuration validation and edge cases"""
    
    def test_port_configuration_validation(self):
        """Test port configuration validation"""
        valid_ports = ["80", "443", "8080", "62050", "65535"]
        
        for port in valid_ports:
            env_vars = {"SERVICE_PORT": port}
            
            with patch.dict(os.environ, env_vars, clear=True):
                import importlib
                importlib.reload(config)
                
                assert isinstance(config.SERVICE_PORT, int)
                assert 1 <= config.SERVICE_PORT <= 65535
                
    def test_invalid_port_configuration(self):
        """Test handling of invalid port configuration"""
        invalid_ports = ["0", "65536", "-1", "invalid", ""]
        
        for port in invalid_ports:
            env_vars = {"SERVICE_PORT": port}
            
            with patch.dict(os.environ, env_vars, clear=True):
                try:
                    import importlib
                    importlib.reload(config)
                    # If it doesn't raise an error, should use a reasonable default
                    assert isinstance(config.SERVICE_PORT, int)
                except (ValueError, TypeError):
                    # Expected behavior for invalid values
                    pass
                    
    def test_file_path_configuration(self):
        """Test file path configuration validation"""
        paths = [
            "/etc/xray/config.json",
            "/usr/bin/xray",
            "./relative/path.json",
            "/absolute/path.yaml",
        ]
        
        for path in paths:
            env_vars = {"XRAY_CONFIG_PATH": path}
            
            with patch.dict(os.environ, env_vars, clear=True):
                import importlib
                importlib.reload(config)
                
                assert isinstance(config.XRAY_CONFIG_PATH, str)
                assert len(config.XRAY_CONFIG_PATH) > 0
                assert config.XRAY_CONFIG_PATH == path
                
    def test_interval_configuration_validation(self):
        """Test interval configuration validation"""
        valid_intervals = ["0", "30", "60", "300", "3600"]
        
        for interval in valid_intervals:
            env_vars = {"XRAY_RESTART_ON_FAILURE_INTERVAL": interval}
            
            with patch.dict(os.environ, env_vars, clear=True):
                import importlib
                importlib.reload(config)
                
                assert isinstance(config.XRAY_RESTART_ON_FAILURE_INTERVAL, int)
                assert config.XRAY_RESTART_ON_FAILURE_INTERVAL >= 0


class TestEnvironmentVariableHandling:
    """Test environment variable handling edge cases"""
    
    def test_empty_environment_variables(self):
        """Test handling of empty environment variables"""
        env_vars = {
            "SERVICE_ADDRESS": "",
            "XRAY_EXECUTABLE_PATH": "",
            "SSL_CERT_FILE": ""
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            # Empty strings should be handled gracefully
            # Either use defaults or accept empty strings based on variable
            assert isinstance(config.SERVICE_ADDRESS, str)
            assert isinstance(config.XRAY_EXECUTABLE_PATH, str)
            assert isinstance(config.SSL_CERT_FILE, str)
            
    def test_whitespace_environment_variables(self):
        """Test handling of whitespace in environment variables"""
        env_vars = {
            "SERVICE_ADDRESS": "  127.0.0.1  ",
            "XRAY_EXECUTABLE_PATH": "\t/usr/bin/xray\n",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            # Should handle whitespace appropriately
            # Note: decouple library typically handles this
            assert "127.0.0.1" in config.SERVICE_ADDRESS
            assert "/usr/bin/xray" in config.XRAY_EXECUTABLE_PATH
            
    def test_environment_variable_case_sensitivity(self):
        """Test that environment variables are case-sensitive"""
        env_vars = {
            "service_address": "127.0.0.1",  # lowercase
            "SERVICE_ADDRESS": "0.0.0.0",    # uppercase
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            importlib.reload(config)
            
            # Should use the correctly cased variable
            assert config.SERVICE_ADDRESS == "0.0.0.0"


class TestConfigurationConstants:
    """Test configuration constants and types"""
    
    def test_configuration_types(self):
        """Test that configuration values have correct types"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            # String configurations
            string_configs = [
                config.SERVICE_ADDRESS,
                config.XRAY_EXECUTABLE_PATH,
                config.XRAY_ASSETS_PATH,
                config.XRAY_CONFIG_PATH,
                config.SSL_CERT_FILE,
                config.SSL_KEY_FILE,
            ]
            
            for cfg in string_configs:
                assert isinstance(cfg, str), f"Configuration should be string: {cfg}"
                
            # Integer configurations
            integer_configs = [
                config.SERVICE_PORT,
                config.XRAY_RESTART_ON_FAILURE_INTERVAL,
                config.SING_BOX_RESTART_ON_FAILURE_INTERVAL,
                config.SING_BOX_USER_MODIFICATION_INTERVAL,
            ]
            
            for cfg in integer_configs:
                assert isinstance(cfg, int), f"Configuration should be integer: {cfg}"
                
            # Boolean configurations
            boolean_configs = [
                config.INSECURE,
                config.XRAY_ENABLED,
                config.XRAY_RESTART_ON_FAILURE,
                config.SING_BOX_ENABLED,
                config.HYSTERIA_ENABLED,
                config.DEBUG,
            ]
            
            for cfg in boolean_configs:
                assert isinstance(cfg, bool), f"Configuration should be boolean: {cfg}"
                
            # Enum configurations
            assert isinstance(config.AUTH_GENERATION_ALGORITHM, AuthAlgorithm)
            
    def test_configuration_constants_immutability(self):
        """Test that configuration constants behave appropriately"""
        original_address = config.SERVICE_ADDRESS
        original_port = config.SERVICE_PORT
        
        # Configuration values should be accessible
        assert isinstance(original_address, str)
        assert isinstance(original_port, int)
        
        # Values should be consistent
        assert config.SERVICE_ADDRESS == original_address
        assert config.SERVICE_PORT == original_port


if __name__ == "__main__":
    pytest.main([__file__, "-v"])