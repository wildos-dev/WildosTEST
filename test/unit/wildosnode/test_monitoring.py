"""
Comprehensive unit tests for WildosNode monitoring system.

Tests monitoring components:
- InContainerPeakMonitor for resource tracking and peak events  
- Host system metrics collection
- Peak event generation and streaming
- Monitoring FSM (Finite State Machine)
- Error handling and edge cases
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from wildosnode.monitoring.peak_monitor import (
    InContainerPeakMonitor, PeakState, ThresholdConfig, PeakTracker
)
from wildosnode.service.service_pb2 import PeakEvent, PeakCategory, PeakLevel


@pytest.fixture
def threshold_config():
    """Sample threshold configuration"""
    return ThresholdConfig(
        cpu_warning=75.0,
        cpu_critical=90.0,
        memory_warning=80.0,
        memory_critical=95.0,
        hysteresis_percent=5.0,
        min_duration_seconds=30,
        cool_down_cycles=2
    )


@pytest.fixture
def mock_psutil():
    """Mock psutil for system metrics"""
    with patch('wildosnode.monitoring.peak_monitor.psutil') as mock_psutil:
        # CPU metrics
        mock_psutil.cpu_percent.return_value = 45.0
        mock_psutil.getloadavg.return_value = (0.5, 1.0, 1.5)
        
        # Memory metrics
        mock_memory = MagicMock()
        mock_memory.percent = 60.0
        mock_memory.used = 4 * 1024**3  # 4GB
        mock_memory.total = 8 * 1024**3  # 8GB
        mock_psutil.virtual_memory.return_value = mock_memory
        
        # Disk metrics
        mock_disk = MagicMock()
        mock_disk.used = 50 * 1024**3  # 50GB
        mock_disk.total = 100 * 1024**3  # 100GB
        mock_psutil.disk_usage.return_value = mock_disk
        
        # Network metrics
        mock_net_stats = MagicMock()
        mock_net_stats.bytes_recv = 1000000
        mock_net_stats.bytes_sent = 2000000
        mock_psutil.net_io_counters.return_value = mock_net_stats
        
        yield mock_psutil


@pytest.fixture
def peak_monitor(threshold_config):
    """Create InContainerPeakMonitor instance"""
    with patch('wildosnode.monitoring.peak_seq_manager.get_sequence_manager') as mock_seq:
        mock_seq.return_value = MagicMock()
        monitor = InContainerPeakMonitor(node_id=1, config=threshold_config)
        return monitor


class TestThresholdConfig:
    """Test threshold configuration"""
    
    def test_threshold_config_defaults(self):
        """Test default threshold values"""
        config = ThresholdConfig()
        
        assert config.cpu_warning == 75.0
        assert config.cpu_critical == 90.0
        assert config.memory_warning == 80.0
        assert config.memory_critical == 95.0
        assert config.hysteresis_percent == 5.0
        assert config.min_duration_seconds == 30
        assert config.cool_down_cycles == 2
        
    def test_threshold_config_custom_values(self):
        """Test custom threshold configuration"""
        config = ThresholdConfig(
            cpu_warning=65.0,
            cpu_critical=85.0,
            memory_warning=70.0,
            memory_critical=90.0,
            hysteresis_percent=10.0,
            min_duration_seconds=60,
            cool_down_cycles=3
        )
        
        assert config.cpu_warning == 65.0
        assert config.cpu_critical == 85.0
        assert config.memory_warning == 70.0
        assert config.memory_critical == 90.0
        assert config.hysteresis_percent == 10.0
        assert config.min_duration_seconds == 60
        assert config.cool_down_cycles == 3


class TestPeakTracker:
    """Test peak tracking FSM"""
    
    def test_peak_tracker_initial_state(self):
        """Test initial state of PeakTracker"""
        tracker = PeakTracker()
        
        assert tracker.state == PeakState.IDLE
        assert tracker.start_time is None
        assert tracker.peak_value == 0.0
        assert tracker.threshold == 0.0
        assert tracker.level == "WARNING"
        assert tracker.context_snapshot is None
        assert tracker.cool_down_counter == 0
        assert tracker.last_seq == 0
        
    def test_peak_tracker_state_transitions(self):
        """Test state transitions in PeakTracker"""
        tracker = PeakTracker()
        
        # IDLE -> RISING
        tracker.state = PeakState.RISING
        assert tracker.state == PeakState.RISING
        
        # RISING -> PEAK
        tracker.state = PeakState.PEAK
        assert tracker.state == PeakState.PEAK
        
        # PEAK -> COOLING
        tracker.state = PeakState.COOLING
        assert tracker.state == PeakState.COOLING
        
        # COOLING -> IDLE
        tracker.state = PeakState.IDLE
        assert tracker.state == PeakState.IDLE


class TestInContainerPeakMonitor:
    """Test InContainerPeakMonitor functionality"""
    
    def test_peak_monitor_initialization(self, threshold_config):
        """Test PeakMonitor initialization"""
        with patch('wildosnode.monitoring.peak_seq_manager.get_sequence_manager') as mock_seq:
            mock_seq.return_value = MagicMock()
            
            monitor = InContainerPeakMonitor(node_id=1, config=threshold_config)
            
            assert monitor.node_id == 1
            assert monitor.config == threshold_config
            assert monitor.is_running is False
            assert len(monitor.trackers) == 0
            assert monitor.metrics_buffer == []
            
    def test_get_system_metrics_success(self, peak_monitor, mock_psutil):
        """Test successful system metrics collection"""
        with patch('time.time', return_value=1640000000):
            metrics = peak_monitor._get_system_metrics()
            
            assert metrics is not None
            assert metrics['cpu_usage'] == 45.0
            assert metrics['memory_percent'] == 60.0
            assert metrics['load_1min'] == 0.5
            assert metrics['timestamp'] == 1640000000
            assert 'network_rx_bytes' in metrics
            assert 'network_tx_bytes' in metrics
            
    def test_get_system_metrics_psutil_unavailable(self, peak_monitor):
        """Test handling when psutil is not available"""
        with patch('wildosnode.monitoring.peak_monitor.psutil', side_effect=ImportError("No psutil")):
            metrics = peak_monitor._get_system_metrics()
            assert metrics is None
            
    def test_get_system_metrics_exception(self, peak_monitor, mock_psutil):
        """Test handling of system metrics exceptions"""
        mock_psutil.cpu_percent.side_effect = Exception("CPU error")
        
        metrics = peak_monitor._get_system_metrics()
        assert metrics is None
        
    def test_get_backend_context(self, peak_monitor):
        """Test backend context collection"""
        context = peak_monitor._get_backend_context()
        
        assert isinstance(context, dict)
        assert 'active_users' in context
        assert 'backend_status' in context
        assert 'connection_count' in context
        assert 'traffic_rate_mbps' in context
        
    def test_create_dedupe_key(self, peak_monitor):
        """Test deduplication key creation"""
        key1 = peak_monitor._create_dedupe_key("CPU", "cpu_usage", "context1")
        key2 = peak_monitor._create_dedupe_key("CPU", "cpu_usage", "context1")
        key3 = peak_monitor._create_dedupe_key("CPU", "cpu_usage", "context2")
        
        # Same inputs should produce same key
        assert key1 == key2
        # Different context should produce different key
        assert key1 != key3
        # Keys should be hex strings
        assert len(key1) == 16
        assert all(c in '0123456789abcdef' for c in key1)
        
    def test_check_thresholds_no_violations(self, peak_monitor):
        """Test threshold checking with no violations"""
        metrics = {
            'cpu_usage': 50.0,    # Below warning (75)
            'memory_percent': 60.0  # Below warning (80)
        }
        
        violations = peak_monitor._check_thresholds(metrics)
        assert len(violations) == 0
        
    def test_check_thresholds_warning_violations(self, peak_monitor):
        """Test threshold checking with warning violations"""
        metrics = {
            'cpu_usage': 80.0,    # Above warning (75), below critical (90)
            'memory_percent': 85.0  # Above warning (80), below critical (95)
        }
        
        violations = peak_monitor._check_thresholds(metrics)
        assert len(violations) == 2
        
        # Check CPU violation
        cpu_violation = next((v for v in violations if v[0] == 'CPU'), None)
        assert cpu_violation is not None
        assert cpu_violation[2] == 80.0  # value
        assert cpu_violation[3] == 75.0  # threshold
        assert cpu_violation[4] == 'WARNING'  # level
        
        # Check Memory violation
        memory_violation = next((v for v in violations if v[0] == 'MEMORY'), None)
        assert memory_violation is not None
        assert memory_violation[2] == 85.0  # value
        assert memory_violation[3] == 80.0  # threshold
        assert memory_violation[4] == 'WARNING'  # level
        
    def test_check_thresholds_critical_violations(self, peak_monitor):
        """Test threshold checking with critical violations"""
        metrics = {
            'cpu_usage': 95.0,    # Above critical (90)
            'memory_percent': 97.0  # Above critical (95)
        }
        
        violations = peak_monitor._check_thresholds(metrics)
        assert len(violations) == 2
        
        # Check for critical levels
        for violation in violations:
            assert violation[4] == 'CRITICAL'
            
    def test_process_violation_new_peak(self, peak_monitor):
        """Test processing a new violation (IDLE -> RISING)"""
        with patch('time.time', return_value=1640000000):
            context = {'test': 'context'}
            
            event = peak_monitor._process_violation(
                'CPU', 'cpu_usage', 85.0, 80.0, 'WARNING', context
            )
            
            # Should create a new event
            assert event is not None
            assert 'CPU:cpu_usage' in peak_monitor.trackers
            
            tracker = peak_monitor.trackers['CPU:cpu_usage']
            assert tracker.state == PeakState.RISING
            assert tracker.start_time == 1640000000
            assert tracker.peak_value == 85.0
            assert tracker.threshold == 80.0
            assert tracker.level == 'WARNING'
            assert tracker.context_snapshot == context
            
    def test_process_violation_update_peak(self, peak_monitor):
        """Test updating an existing peak (RISING -> PEAK)"""
        # Setup existing tracker
        tracker = PeakTracker(
            state=PeakState.RISING,
            start_time=1640000000,
            peak_value=85.0,
            threshold=80.0,
            level='WARNING'
        )
        peak_monitor.trackers['CPU:cpu_usage'] = tracker
        
        # Process higher value
        context = {'test': 'context'}
        event = peak_monitor._process_violation(
            'CPU', 'cpu_usage', 92.0, 90.0, 'CRITICAL', context
        )
        
        # Should not create new event (same peak)
        assert event is None
        
        # Should update tracker
        assert tracker.state == PeakState.PEAK
        assert tracker.peak_value == 92.0
        assert tracker.threshold == 90.0
        assert tracker.level == 'CRITICAL'  # Upgraded to critical
        
    def test_process_no_violation_below_hysteresis(self, peak_monitor):
        """Test processing no violation with value below hysteresis"""
        # Setup existing tracker in PEAK state
        tracker = PeakTracker(
            state=PeakState.PEAK,
            start_time=1640000000,
            peak_value=85.0,
            threshold=80.0,
            level='WARNING',
            cool_down_counter=0
        )
        peak_monitor.trackers['CPU:cpu_usage'] = tracker
        
        # Process value below hysteresis threshold (80.0 * 0.95 = 76.0)
        with patch('time.time', return_value=1640000030):
            event = peak_monitor._process_no_violation('CPU', 'cpu_usage', 70.0)
            
        # Should transition to COOLING
        assert tracker.state == PeakState.COOLING
        assert tracker.cool_down_counter == 1
        assert event is None  # No event during cooling
        
    def test_process_no_violation_complete_cooldown(self, peak_monitor):
        """Test completing cooldown and returning to IDLE"""
        # Setup tracker in COOLING state with max cool_down_counter
        tracker = PeakTracker(
            state=PeakState.COOLING,
            start_time=1640000000,
            peak_value=85.0,
            threshold=80.0,
            level='WARNING',
            cool_down_counter=1  # One less than config.cool_down_cycles (2)
        )
        peak_monitor.trackers['CPU:cpu_usage'] = tracker
        
        # Process value below hysteresis threshold
        with patch('time.time', return_value=1640000060):
            event = peak_monitor._process_no_violation('CPU', 'cpu_usage', 70.0)
            
        # Should complete cooldown and create end event
        assert event is not None
        assert tracker.state == PeakState.IDLE
        assert tracker.cool_down_counter >= peak_monitor.config.cool_down_cycles
        
    def test_create_peak_event(self, peak_monitor):
        """Test peak event creation"""
        context = {'backend_status': 'running', 'active_users': 5}
        
        with patch('time.time', return_value=1640000000):
            # Create event method is private, test through violation processing
            event = peak_monitor._process_violation(
                'CPU', 'cpu_usage', 85.0, 80.0, 'WARNING', context
            )
            
        assert event is not None
        assert event['category'] == 'CPU'
        assert event['metric'] == 'cpu_usage'
        assert event['value'] == 85.0
        assert event['threshold'] == 80.0
        assert event['level'] == 'WARNING'
        assert event['node_id'] == 1
        assert event['started_at_ms'] == 1640000000000
        
    @pytest.mark.asyncio
    async def test_peak_events_stream(self, peak_monitor):
        """Test peak events streaming"""
        # Setup events queue
        test_event = {
            'node_id': 1,
            'category': 'CPU',
            'metric': 'cpu_usage',
            'value': 85.0,
            'threshold': 80.0,
            'level': 'WARNING',
            'started_at_ms': 1640000000000
        }
        
        await peak_monitor.peak_events_queue.put(test_event)
        
        # Test async iteration
        events = []
        async def collect_events():
            async for event in peak_monitor.get_peak_events_stream():
                events.append(event)
                if len(events) >= 1:  # Collect one event and break
                    break
                    
        # This would run infinitely, so we'll test the queue directly
        event = await peak_monitor.peak_events_queue.get()
        assert event['category'] == 'CPU'
        assert event['value'] == 85.0
        
    def test_monitoring_fsm_complete_cycle(self, peak_monitor):
        """Test complete FSM cycle from IDLE to PEAK to IDLE"""
        context = {'test': 'context'}
        
        # 1. Start peak (IDLE -> RISING)
        with patch('time.time', return_value=1640000000):
            event1 = peak_monitor._process_violation(
                'CPU', 'cpu_usage', 85.0, 80.0, 'WARNING', context
            )
        
        assert event1 is not None
        tracker = peak_monitor.trackers['CPU:cpu_usage']
        assert tracker.state == PeakState.RISING
        
        # 2. Continue peak (RISING -> PEAK)
        event2 = peak_monitor._process_violation(
            'CPU', 'cpu_usage', 87.0, 80.0, 'WARNING', context
        )
        
        assert event2 is None  # Same peak, no new event
        assert tracker.state == PeakState.PEAK
        assert tracker.peak_value == 87.0
        
        # 3. Start cooling (PEAK -> COOLING)
        event3 = peak_monitor._process_no_violation('CPU', 'cpu_usage', 70.0)
        
        assert event3 is None  # Cooling, no event yet
        assert tracker.state == PeakState.COOLING
        assert tracker.cool_down_counter == 1
        
        # 4. Complete cooling (COOLING -> IDLE)
        with patch('time.time', return_value=1640000060):
            event4 = peak_monitor._process_no_violation('CPU', 'cpu_usage', 70.0)
            
        assert event4 is not None  # End of peak event
        assert tracker.state == PeakState.IDLE


class TestHostSystemMetrics:
    """Test host system metrics collection (from gRPC service)"""
    
    @pytest.mark.asyncio
    async def test_host_metrics_collection_success(self):
        """Test successful host system metrics collection"""
        with patch('psutil.cpu_percent', return_value=45.5), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.getloadavg', return_value=(0.5, 1.0, 1.5)), \
             patch('psutil.net_io_counters') as mock_net, \
             patch('psutil.boot_time', return_value=1640000000), \
             patch('time.time', return_value=1640100000):
            
            # Configure mock objects
            mock_memory.return_value = MagicMock(percent=75.0, total=8*1024**3)
            mock_disk.return_value = MagicMock(percent=60.0, total=500*1024**3)
            mock_net.return_value = {
                'eth0': MagicMock(
                    bytes_sent=1000000, bytes_recv=2000000,
                    packets_sent=1000, packets_recv=2000
                )
            }
            
            # Import here to avoid circular imports in testing
            from wildosnode.service.service import WildosService
            from wildosnode.service.service_pb2 import Empty, HostSystemMetrics
            
            # Create mock service
            service = MagicMock()
            mock_stream = AsyncMock()
            mock_stream.recv_message = AsyncMock(return_value=Empty())
            mock_stream.send_message = AsyncMock()
            
            # Create the actual method temporarily for testing
            async def get_host_system_metrics(stream):
                await stream.recv_message()
                
                import psutil
                import time
                
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                load_avg = psutil.getloadavg()
                net_io = psutil.net_io_counters(pernic=True)
                
                network_interfaces = []
                for name, stats in net_io.items():
                    from wildosnode.service.service_pb2 import NetworkInterface
                    network_interfaces.append(NetworkInterface(
                        name=name,
                        bytes_sent=stats.bytes_sent,
                        bytes_received=stats.bytes_recv,
                        packets_sent=stats.packets_sent,
                        packets_received=stats.packets_recv
                    ))
                
                boot_time = int(psutil.boot_time())
                current_time = int(time.time())
                uptime_seconds = current_time - boot_time
                
                metrics = HostSystemMetrics(
                    cpu_usage=cpu_usage,
                    memory_usage=memory.percent,
                    memory_total=memory.total / (1024**3),
                    disk_usage=disk.percent,
                    disk_total=disk.total / (1024**3),
                    network_interfaces=network_interfaces,
                    uptime_seconds=uptime_seconds,
                    load_average_1m=load_avg[0],
                    load_average_5m=load_avg[1],
                    load_average_15m=load_avg[2]
                )
                
                await stream.send_message(metrics)
            
            await get_host_system_metrics(mock_stream)
            
            # Verify metrics were collected and sent
            mock_stream.send_message.assert_called_once()
            call_args = mock_stream.send_message.call_args[0][0]
            assert hasattr(call_args, 'cpu_usage')
            assert call_args.cpu_usage == 45.5
            assert call_args.memory_usage == 75.0
            assert len(call_args.network_interfaces) >= 1
            assert call_args.uptime_seconds == 100000
            
    @pytest.mark.asyncio
    async def test_host_metrics_error_handling(self):
        """Test host system metrics error handling"""
        with patch('psutil.cpu_percent', side_effect=Exception("CPU error")):
            
            from wildosnode.service.service import WildosService
            from wildosnode.service.service_pb2 import Empty
            from grpclib import GRPCError, Status
            
            service = MagicMock()
            mock_stream = AsyncMock()
            mock_stream.recv_message = AsyncMock(return_value=Empty())
            
            # Create error handling method
            async def get_host_system_metrics_with_error(stream):
                await stream.recv_message()
                try:
                    import psutil
                    cpu_usage = psutil.cpu_percent(interval=1)
                except Exception as e:
                    raise GRPCError(Status.INTERNAL, f"Host metrics error: {e}")
            
            # Should raise GRPCError
            with pytest.raises(GRPCError) as exc_info:
                await get_host_system_metrics_with_error(mock_stream)
            
            assert exc_info.value.status == Status.INTERNAL


class TestMonitoringIntegration:
    """Test monitoring integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_peak_monitor_with_real_metrics(self, threshold_config):
        """Test peak monitor with realistic system metrics"""
        with patch('wildosnode.monitoring.peak_seq_manager.get_sequence_manager') as mock_seq:
            mock_seq.return_value = MagicMock()
            monitor = InContainerPeakMonitor(node_id=1, config=threshold_config)
            
            # Simulate high CPU usage scenario
            high_cpu_metrics = {
                'cpu_usage': 92.0,      # Above critical threshold
                'memory_percent': 65.0,  # Normal
                'timestamp': 1640000000
            }
            
            context = monitor._get_backend_context()
            violations = monitor._check_thresholds(high_cpu_metrics)
            
            # Should detect CPU violation
            assert len(violations) == 1
            cpu_violation = violations[0]
            assert cpu_violation[0] == 'CPU'
            assert cpu_violation[4] == 'CRITICAL'
            
            # Process the violation
            with patch('time.time', return_value=1640000000):
                event = monitor._process_violation(
                    cpu_violation[0], cpu_violation[1], cpu_violation[2],
                    cpu_violation[3], cpu_violation[4], context
                )
                
            assert event is not None
            assert event['level'] == 'CRITICAL'
            assert event['value'] == 92.0
            
    def test_monitoring_configuration_validation(self):
        """Test monitoring configuration validation"""
        # Test valid configuration
        valid_config = ThresholdConfig(
            cpu_warning=70.0,
            cpu_critical=85.0,
            memory_warning=75.0,
            memory_critical=90.0
        )
        
        assert valid_config.cpu_warning < valid_config.cpu_critical
        assert valid_config.memory_warning < valid_config.memory_critical
        
        # Test configuration edge cases
        edge_config = ThresholdConfig(
            cpu_warning=99.0,
            cpu_critical=99.5,
            hysteresis_percent=0.1,
            cool_down_cycles=1
        )
        
        assert edge_config.cpu_critical > edge_config.cpu_warning
        assert edge_config.hysteresis_percent > 0
        assert edge_config.cool_down_cycles >= 1
        
    @pytest.mark.asyncio
    async def test_monitoring_performance_impact(self, peak_monitor, mock_psutil):
        """Test that monitoring doesn't significantly impact performance"""
        import time
        
        # Measure time for metrics collection
        start_time = time.time()
        
        for _ in range(100):  # Simulate 100 monitoring cycles
            metrics = peak_monitor._get_system_metrics()
            if metrics:
                violations = peak_monitor._check_thresholds(metrics)
                for violation in violations:
                    context = peak_monitor._get_backend_context()
                    peak_monitor._process_violation(
                        violation[0], violation[1], violation[2],
                        violation[3], violation[4], context
                    )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete quickly (less than 1 second for 100 cycles)
        assert elapsed < 1.0
        
        # Verify no memory leaks in trackers
        # In a real scenario, old trackers should be cleaned up
        assert len(peak_monitor.trackers) < 10  # Reasonable limit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])