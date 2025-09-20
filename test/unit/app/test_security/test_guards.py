"""
Unit tests for security guards (app/security/guards.py)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, Request, status
from datetime import datetime, timedelta

from app.security.guards import (
    SecurityGuard,
    security_guard,
    RequireSudoAdmin,
    RequireAdminAccess
)
from app.models.admin import Admin


class TestSecurityGuard:
    """Test SecurityGuard class functionality"""
    
    def test_security_guard_initialization(self):
        """Test SecurityGuard proper initialization"""
        guard = SecurityGuard()
        
        assert guard.failed_attempts == {}
        assert guard.lockout_threshold == 5
        assert guard.lockout_duration == 300  # 5 minutes
    
    def test_get_lockout_key_admin(self):
        """Test lockout key generation for admin"""
        guard = SecurityGuard()
        admin = Mock()
        admin.username = "test_admin"
        
        key = guard._get_lockout_key(None, admin)
        
        assert key == "admin:test_admin"
    
    def test_get_lockout_key_ip(self):
        """Test lockout key generation for IP"""
        guard = SecurityGuard()
        request = Mock()
        
        with patch('app.security.guards.get_client_ip', return_value="192.168.1.100"):
            key = guard._get_lockout_key(request, None)
        
        assert key == "ip:192.168.1.100"
    
    def test_record_failed_attempt(self):
        """Test recording failed authentication attempts"""
        guard = SecurityGuard()
        key = "test_key"
        
        guard._record_failed_attempt(key)
        
        assert key in guard.failed_attempts
        assert len(guard.failed_attempts[key]['attempts']) == 1
        assert isinstance(guard.failed_attempts[key]['attempts'][0], datetime)
    
    def test_clear_failed_attempts(self):
        """Test clearing failed attempts after successful auth"""
        guard = SecurityGuard()
        key = "test_key"
        
        # Record some failed attempts
        guard._record_failed_attempt(key)
        guard._record_failed_attempt(key)
        assert key in guard.failed_attempts
        
        # Clear attempts
        guard._clear_failed_attempts(key)
        
        assert key not in guard.failed_attempts
    
    def test_is_locked_out_false(self):
        """Test lockout check returns False when not locked out"""
        guard = SecurityGuard()
        key = "test_key"
        
        # Record fewer attempts than threshold
        for i in range(3):
            guard._record_failed_attempt(key)
        
        is_locked = guard._is_locked_out(key)
        
        assert is_locked == False
    
    def test_is_locked_out_true(self):
        """Test lockout check returns True when locked out"""
        guard = SecurityGuard()
        guard.lockout_threshold = 3  # Lower threshold for testing
        key = "test_key"
        
        # Record attempts equal to threshold
        for i in range(3):
            guard._record_failed_attempt(key)
        
        is_locked = guard._is_locked_out(key)
        
        assert is_locked == True
    
    def test_is_locked_out_expired(self):
        """Test lockout expires after duration"""
        guard = SecurityGuard()
        guard.lockout_threshold = 2
        guard.lockout_duration = 1  # 1 second for testing
        key = "test_key"
        
        # Record attempts to trigger lockout
        for i in range(2):
            guard._record_failed_attempt(key)
        
        assert guard._is_locked_out(key) == True
        
        # Wait for lockout to expire
        import time
        time.sleep(1.1)
        
        is_locked = guard._is_locked_out(key)
        
        assert is_locked == False
    
    def test_cleanup_old_attempts(self):
        """Test cleanup of old failed attempts"""
        guard = SecurityGuard()
        guard.lockout_duration = 60  # 1 minute
        
        # Add old attempt
        old_time = datetime.utcnow() - timedelta(seconds=120)  # 2 minutes ago
        guard.failed_attempts["old_key"] = {
            'attempts': [old_time]
        }
        
        # Add recent attempt
        guard._record_failed_attempt("recent_key")
        
        # Check lockout (triggers cleanup)
        guard._is_locked_out("old_key")
        
        # Old attempts should be cleaned up
        assert len(guard.failed_attempts["old_key"]['attempts']) == 0


class TestSudoAdminGuard:
    """Test sudo admin requirement guard"""
    
    @pytest.mark.asyncio
    async def test_require_sudo_admin_success(self):
        """Test successful sudo admin validation"""
        guard = SecurityGuard()
        admin = Mock()
        admin.id = 1
        admin.username = "sudo_admin"
        admin.is_sudo = True
        
        request = Mock()
        
        @guard.require_sudo_admin("delete", "users")
        async def protected_function(admin, request):
            return {"status": "success"}
        
        with patch('app.security.guards.get_client_ip', return_value="127.0.0.1"), \
             patch('app.security.security_logger.security_logger') as mock_logger:
            
            result = await protected_function(admin, request)
            
            assert result == {"status": "success"}
            mock_logger.log_security_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_require_sudo_admin_insufficient_privileges(self):
        """Test sudo admin requirement with non-sudo admin"""
        guard = SecurityGuard()
        admin = Mock()
        admin.id = 1
        admin.username = "regular_admin"
        admin.is_sudo = False
        
        request = Mock()
        
        @guard.require_sudo_admin("delete", "users")
        async def protected_function(admin, request):
            return {"status": "success"}
        
        with patch('app.security.guards.get_client_ip', return_value="127.0.0.1"), \
             patch('app.security.security_logger.security_logger') as mock_logger, \
             pytest.raises(HTTPException) as exc_info:
            
            await protected_function(admin, request)
        
        assert exc_info.value.status_code == 403
        assert "sudo admin privileges required" in exc_info.value.detail.lower()
        mock_logger.log_security_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_require_sudo_admin_locked_out(self):
        """Test sudo admin requirement when account is locked out"""
        guard = SecurityGuard()
        admin = Mock()
        admin.id = 1
        admin.username = "locked_admin"
        admin.is_sudo = True
        
        request = Mock()
        
        # Mock lockout condition
        guard.failed_attempts["admin:locked_admin"] = {
            'attempts': [datetime.utcnow() for _ in range(10)]
        }
        
        @guard.require_sudo_admin("delete", "users")
        async def protected_function(admin, request):
            return {"status": "success"}
        
        with patch('app.security.guards.get_client_ip', return_value="127.0.0.1"), \
             patch('app.security.security_logger.security_logger') as mock_logger, \
             pytest.raises(HTTPException) as exc_info:
            
            await protected_function(admin, request)
        
        assert exc_info.value.status_code == 423
        assert "locked" in exc_info.value.detail.lower()
        mock_logger.log_security_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_require_sudo_admin_no_admin(self):
        """Test sudo admin requirement with no admin provided"""
        guard = SecurityGuard()
        
        @guard.require_sudo_admin("delete", "users")
        async def protected_function():
            return {"status": "success"}
        
        with pytest.raises(HTTPException) as exc_info:
            await protected_function()
        
        assert exc_info.value.status_code == 401
        assert "authentication required" in exc_info.value.detail.lower()


class TestAdminAccessGuard:
    """Test admin access requirement guard"""
    
    @pytest.mark.asyncio
    async def test_require_admin_access_success(self):
        """Test successful admin access validation"""
        guard = SecurityGuard()
        admin = Mock()
        admin.id = 1
        admin.username = "admin"
        admin.enabled = True
        admin.is_sudo = False
        admin.modify_users_access = True
        
        request = Mock()
        
        @guard.require_admin_access("read", "users")
        async def protected_function(admin, request):
            return {"status": "success"}
        
        with patch('app.security.guards.get_client_ip', return_value="127.0.0.1"):
            result = await protected_function(admin, request)
            assert result == {"status": "success"}
    
    @pytest.mark.asyncio
    async def test_require_admin_access_disabled_admin(self):
        """Test admin access requirement with disabled admin"""
        guard = SecurityGuard()
        admin = Mock()
        admin.id = 1
        admin.username = "disabled_admin"
        admin.enabled = False
        
        request = Mock()
        
        @guard.require_admin_access("read", "users")
        async def protected_function(admin, request):
            return {"status": "success"}
        
        with patch('app.security.guards.get_client_ip', return_value="127.0.0.1"), \
             patch('app.security.security_logger.security_logger') as mock_logger, \
             pytest.raises(HTTPException) as exc_info:
            
            await protected_function(admin, request)
        
        assert exc_info.value.status_code == 403
        assert "disabled" in exc_info.value.detail.lower()
        mock_logger.log_security_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_require_admin_access_insufficient_modify_permission(self):
        """Test admin access with insufficient modify users permission"""
        guard = SecurityGuard()
        admin = Mock()
        admin.id = 1
        admin.username = "limited_admin"
        admin.enabled = True
        admin.is_sudo = False
        admin.modify_users_access = False
        
        request = Mock()
        
        @guard.require_admin_access("modify", "users", allow_modify_access=True)
        async def protected_function(admin, request):
            return {"status": "success"}
        
        with patch('app.security.guards.get_client_ip', return_value="127.0.0.1"), \
             patch('app.security.security_logger.security_logger') as mock_logger, \
             pytest.raises(HTTPException) as exc_info:
            
            await protected_function(admin, request)
        
        assert exc_info.value.status_code == 403
        assert "insufficient permissions" in exc_info.value.detail.lower()
        mock_logger.log_security_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_require_admin_access_sudo_bypasses_modify_permission(self):
        """Test that sudo admin bypasses modify_users_access check"""
        guard = SecurityGuard()
        admin = Mock()
        admin.id = 1
        admin.username = "sudo_admin"
        admin.enabled = True
        admin.is_sudo = True
        admin.modify_users_access = False  # Should be bypassed by sudo
        
        request = Mock()
        
        @guard.require_admin_access("modify", "users", allow_modify_access=True)
        async def protected_function(admin, request):
            return {"status": "success"}
        
        with patch('app.security.guards.get_client_ip', return_value="127.0.0.1"):
            result = await protected_function(admin, request)
            assert result == {"status": "success"}


class TestSecurityGuardDependencies:
    """Test FastAPI dependency functions"""
    
    def test_require_sudo_admin_dependency(self):
        """Test RequireSudoAdmin dependency factory"""
        dependency_func = RequireSudoAdmin("delete", "admins")
        
        assert callable(dependency_func)
        # The actual dependency would need SudoAdminDep and Request
        # This tests the factory function creation
    
    def test_require_admin_access_dependency(self):
        """Test RequireAdminAccess dependency factory"""
        dependency_func = RequireAdminAccess("read", "users")
        
        assert callable(dependency_func)
        # The actual dependency would need AdminDep and Request
        # This tests the factory function creation
    
    @patch('app.security.security_logger.security_logger')
    @patch('app.security.guards.get_client_ip')
    def test_require_admin_access_dependency_execution(self, mock_get_ip, mock_logger):
        """Test RequireAdminAccess dependency execution"""
        mock_get_ip.return_value = "127.0.0.1"
        
        # Create dependency
        dependency_func = RequireAdminAccess("read", "users")
        
        # Mock admin and request
        admin = Mock()
        admin.id = 1
        admin.username = "test_admin"
        admin.enabled = True
        
        request = Mock()
        
        # Execute dependency
        result = dependency_func.dependency(admin, request)
        
        assert result == admin
        mock_logger.log_security_event.assert_called()
    
    @patch('app.security.security_logger.security_logger')
    @patch('app.security.guards.get_client_ip')
    def test_require_admin_access_dependency_disabled_admin(self, mock_get_ip, mock_logger):
        """Test RequireAdminAccess dependency with disabled admin"""
        mock_get_ip.return_value = "127.0.0.1"
        
        dependency_func = RequireAdminAccess("read", "users")
        
        admin = Mock()
        admin.id = 1
        admin.username = "disabled_admin"
        admin.enabled = False
        
        request = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            dependency_func.dependency(admin, request)
        
        assert exc_info.value.status_code == 403
        mock_logger.log_security_event.assert_called()


class TestSecurityGuardIntegration:
    """Test security guard integration scenarios"""
    
    def test_global_security_guard_instance(self):
        """Test global security guard instance"""
        from app.security.guards import security_guard
        
        assert isinstance(security_guard, SecurityGuard)
        assert security_guard.lockout_threshold == 5
        assert security_guard.lockout_duration == 300
    
    def test_concurrent_failed_attempts(self):
        """Test handling of concurrent failed attempts"""
        guard = SecurityGuard()
        key = "concurrent_test"
        
        # Simulate concurrent failed attempts
        import threading
        
        def record_attempt():
            guard._record_failed_attempt(key)
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=record_attempt)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have recorded all attempts
        assert len(guard.failed_attempts[key]['attempts']) == 10
    
    def test_lockout_across_different_operations(self):
        """Test that lockout applies across different operations"""
        guard = SecurityGuard()
        guard.lockout_threshold = 3
        admin = Mock()
        admin.username = "test_admin"
        admin.is_sudo = True
        
        # Record failed attempts for one operation
        for i in range(3):
            guard._record_failed_attempt("admin:test_admin")
        
        # Different operation should also be blocked
        @guard.require_sudo_admin("create", "services")
        async def another_operation(admin):
            return "success"
        
        with pytest.raises(HTTPException) as exc_info:
            import asyncio
            asyncio.run(another_operation(admin))
        
        assert exc_info.value.status_code == 423


@pytest.mark.parametrize("attempts,threshold,should_be_locked", [
    (2, 5, False),  # Below threshold
    (5, 5, True),   # At threshold
    (7, 5, True),   # Above threshold
    (0, 5, False),  # No attempts
])
def test_lockout_threshold_scenarios(attempts, threshold, should_be_locked):
    """Test various lockout threshold scenarios"""
    guard = SecurityGuard()
    guard.lockout_threshold = threshold
    key = "threshold_test"
    
    for i in range(attempts):
        guard._record_failed_attempt(key)
    
    is_locked = guard._is_locked_out(key)
    
    assert is_locked == should_be_locked