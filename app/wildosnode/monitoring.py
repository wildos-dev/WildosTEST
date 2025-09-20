"""
Enhanced logging and monitoring system for gRPC client operations.

This module provides comprehensive monitoring capabilities including structured logging,
metrics collection, performance monitoring, and alerting integration for Docker VPS environments.
"""

import asyncio
import json
import logging
import time
import traceback
import sys
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Set, Tuple
from datetime import datetime, timezone
import threading
from functools import wraps

from .exceptions import (
    WildosNodeBaseError, ErrorContext, ErrorSeverity, ErrorCategory,
    NetworkError, ServiceError, TimeoutError, AuthenticationError, 
    ConfigurationError, ResourceError
)

logger = logging.getLogger(__name__)

# Monitoring Configuration Constants
METRICS_BUFFER_SIZE = 10000
METRICS_FLUSH_INTERVAL = 60.0  # 1 minute
PERFORMANCE_WINDOW_SIZE = 1000
PERFORMANCE_PERCENTILES = [50, 90, 95, 99]
ALERT_COOLDOWN_SECONDS = 300.0  # 5 minutes per alert type
LOG_CONTEXT_MAX_SIZE = 1000  # Maximum size for context data in logs


class LogLevel(Enum):
    """Extended log levels for structured logging"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class MetricType(Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Structured log entry with enhanced context"""
    timestamp: float = field(default_factory=time.time)
    level: str = "INFO"
    message: str = ""
    logger_name: str = ""
    
    # Operation context
    operation: Optional[str] = None
    node_id: Optional[int] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # Error context (if applicable)
    error_type: Optional[str] = None
    error_category: Optional[str] = None
    error_severity: Optional[str] = None
    error_code: Optional[str] = None
    
    # Performance context
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    # Network context
    remote_address: Optional[str] = None
    remote_port: Optional[int] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    
    # Additional structured data
    tags: Dict[str, str] = field(default_factory=dict)
    fields: Dict[str, Any] = field(default_factory=dict)
    
    # Stack trace (for errors)
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert timestamp to ISO format
        result['timestamp'] = datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()
        # Remove None values to keep logs clean
        return {k: v for k, v in result.items() if v is not None}
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class MetricEntry:
    """Metric data entry"""
    name: str
    type: MetricType
    value: Union[int, float]
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'type': self.type.value,
            'value': self.value,
            'timestamp': self.timestamp,
            'tags': self.tags
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    operation_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    
    # Timing metrics
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    
    # Recent durations for percentile calculations
    recent_durations: deque = field(default_factory=lambda: deque(maxlen=PERFORMANCE_WINDOW_SIZE))
    
    # Error breakdown
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def add_measurement(self, duration_ms: float, success: bool, error_type: Optional[str] = None):
        """Add a performance measurement"""
        self.total_calls += 1
        self.total_duration_ms += duration_ms
        self.recent_durations.append(duration_ms)
        
        if duration_ms < self.min_duration_ms:
            self.min_duration_ms = duration_ms
        if duration_ms > self.max_duration_ms:
            self.max_duration_ms = duration_ms
        
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error_type:
                self.error_counts[error_type] += 1
    
    def get_average_duration(self) -> float:
        """Get average duration"""
        return self.total_duration_ms / self.total_calls if self.total_calls > 0 else 0.0
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        return (self.successful_calls / self.total_calls * 100) if self.total_calls > 0 else 0.0
    
    def get_percentiles(self) -> Dict[int, float]:
        """Calculate percentiles for recent durations"""
        if not self.recent_durations:
            return {}
        
        sorted_durations = sorted(self.recent_durations)
        percentiles = {}
        
        for p in PERFORMANCE_PERCENTILES:
            index = int(len(sorted_durations) * p / 100)
            if index >= len(sorted_durations):
                index = len(sorted_durations) - 1
            percentiles[p] = sorted_durations[index]
        
        return percentiles
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'operation_name': self.operation_name,
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'average_duration_ms': self.get_average_duration(),
            'min_duration_ms': self.min_duration_ms if self.min_duration_ms != float('inf') else 0,
            'max_duration_ms': self.max_duration_ms,
            'success_rate_percent': self.get_success_rate(),
            'percentiles': self.get_percentiles(),
            'error_counts': dict(self.error_counts)
        }


@dataclass 
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: Callable[['MonitoringSystem'], bool]
    severity: AlertSeverity
    message_template: str
    cooldown_seconds: float = ALERT_COOLDOWN_SECONDS
    last_triggered: Optional[float] = None
    
    def should_trigger(self, monitoring_system: 'MonitoringSystem') -> bool:
        """Check if alert should be triggered"""
        # Check cooldown
        if self.last_triggered:
            if (time.time() - self.last_triggered) < self.cooldown_seconds:
                return False
        
        # Check condition
        return self.condition(monitoring_system)
    
    def trigger(self, monitoring_system: 'MonitoringSystem') -> str:
        """Trigger alert and return formatted message"""
        self.last_triggered = time.time()
        
        # Format message with current data
        try:
            return self.message_template.format(
                monitoring_system=monitoring_system,
                error_rate=monitoring_system._get_error_rate(),
                timestamp=datetime.now().isoformat()
            )
        except Exception:
            return self.message_template


class StructuredLogger:
    """Enhanced structured logger with rich context support"""
    
    def __init__(self, name: str, base_logger: Optional[logging.Logger] = None):
        self.name = name
        self.base_logger = base_logger or logging.getLogger(name)
        self._context_stack: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
    
    def with_context(self, **kwargs) -> 'ContextLogger':
        """Create a context logger with additional context"""
        return ContextLogger(self, kwargs)
    
    def log(
        self,
        level: Union[int, LogLevel],
        message: str,
        error: Optional[Exception] = None,
        **context
    ):
        """Log structured message with context"""
        if isinstance(level, LogLevel):
            level_int = level.value
        else:
            level_int = level
        
        # Create log entry
        entry = LogEntry(
            level=logging.getLevelName(level_int),
            message=message,
            logger_name=self.name
        )
        
        # Add current context stack
        with self._lock:
            for ctx in self._context_stack:
                for key, value in ctx.items():
                    if not hasattr(entry, key):
                        entry.fields[key] = value
                    elif key in ['tags', 'fields'] and isinstance(getattr(entry, key), dict):
                        getattr(entry, key).update(value)
                    else:
                        setattr(entry, key, value)
        
        # Add provided context
        for key, value in context.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
            else:
                entry.fields[key] = value
        
        # Add error information if provided
        if error:
            entry.error_type = type(error).__name__
            if isinstance(error, WildosNodeBaseError):
                entry.error_category = error.category.value
                entry.error_severity = error.severity.value
                if error.context:
                    self._merge_error_context(entry, error.context)
            
            # Add stack trace for errors
            if level_int >= logging.ERROR:
                entry.stack_trace = traceback.format_exc()
        
        # Log using base logger
        self.base_logger.log(level_int, entry.to_json())
    
    def _merge_error_context(self, entry: LogEntry, error_context: ErrorContext):
        """Merge error context into log entry"""
        if error_context.node_id:
            entry.node_id = error_context.node_id
        if error_context.operation:
            entry.operation = error_context.operation
        if error_context.duration_ms:
            entry.duration_ms = error_context.duration_ms
        if error_context.remote_address:
            entry.remote_address = error_context.remote_address
        if error_context.remote_port:
            entry.remote_port = error_context.remote_port
        
        # Add metadata to fields
        for key, value in error_context.metadata.items():
            entry.fields[key] = value
    
    def trace(self, message: str, **context):
        """Log trace message"""
        self.log(LogLevel.TRACE, message, **context)
    
    def debug(self, message: str, **context):
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, **context)
    
    def info(self, message: str, **context):
        """Log info message"""
        self.log(LogLevel.INFO, message, **context)
    
    def warning(self, message: str, **context):
        """Log warning message"""
        self.log(LogLevel.WARNING, message, **context)
    
    def error(self, message: str, error: Optional[Exception] = None, **context):
        """Log error message"""
        self.log(LogLevel.ERROR, message, error=error, **context)
    
    def critical(self, message: str, error: Optional[Exception] = None, **context):
        """Log critical message"""
        self.log(LogLevel.CRITICAL, message, error=error, **context)


class ContextLogger:
    """Context logger that adds context to all log messages"""
    
    def __init__(self, parent: StructuredLogger, context: Dict[str, Any]):
        self.parent = parent
        self.context = context
    
    def __enter__(self):
        self.parent._context_stack.append(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        with self.parent._lock:
            if self.parent._context_stack and self.parent._context_stack[-1] == self.context:
                self.parent._context_stack.pop()
    
    def trace(self, message: str, **kwargs):
        """Log trace with context"""
        self.parent.trace(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug with context"""
        self.parent.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info with context"""
        self.parent.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning with context"""
        self.parent.warning(message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error with context"""
        self.parent.error(message, error=error, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical with context"""
        self.parent.critical(message, error=error, **kwargs)


class MetricsCollector:
    """Metrics collection and aggregation system"""
    
    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._buffer: List[MetricEntry] = []
        self._lock = threading.RLock()
        
        # Metrics aggregation
        self._metric_tags: Dict[str, Dict[str, str]] = {}
        
        # Background flush task
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start metrics collection"""
        if self._running:
            return
        
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Metrics collector started")
    
    async def stop(self):
        """Stop metrics collection"""
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self._flush_metrics()
        logger.info("Metrics collector stopped")
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment counter metric"""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
            if tags:
                self._metric_tags[key] = tags
            
            self._buffer.append(MetricEntry(
                name=name,
                type=MetricType.COUNTER,
                value=value,
                tags=tags or {}
            ))
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set gauge metric value"""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
            if tags:
                self._metric_tags[key] = tags
            
            self._buffer.append(MetricEntry(
                name=name,
                type=MetricType.GAUGE,
                value=value,
                tags=tags or {}
            ))
    
    def observe(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Observe histogram metric value"""
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(value)
            if tags:
                self._metric_tags[key] = tags
            
            self._buffer.append(MetricEntry(
                name=name,
                type=MetricType.HISTOGRAM,
                value=value,
                tags=tags or {}
            ))
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value"""
        key = self._make_key(name, tags)
        return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        stats = {
            'count': n,
            'sum': sum(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / n
        }
        
        # Calculate percentiles
        for p in PERFORMANCE_PERCENTILES:
            index = int(n * p / 100)
            if index >= n:
                index = n - 1
            stats[f'p{p}'] = sorted_values[index]
        
        return stats
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        with self._lock:
            result = {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {
                    name: self.get_histogram_stats(name.split('|')[0], 
                                                   self._parse_tags_from_key(name))
                    for name in self._histograms.keys()
                },
                'buffer_size': len(self._buffer)
            }
        
        return result
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create metric key with tags"""
        if not tags:
            return name
        
        tag_str = '|'.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"
    
    def _parse_tags_from_key(self, key: str) -> Optional[Dict[str, str]]:
        """Parse tags from metric key"""
        parts = key.split('|')
        if len(parts) <= 1:
            return None
        
        tags = {}
        for part in parts[1:]:
            if '=' in part:
                k, v = part.split('=', 1)
                tags[k] = v
        
        return tags if tags else None
    
    async def _periodic_flush(self):
        """Periodic metrics flush"""
        while self._running:
            try:
                await asyncio.sleep(METRICS_FLUSH_INTERVAL)
                await self._flush_metrics()
            except Exception as e:
                logger.error(f"Error in metrics flush: {e}")
    
    async def _flush_metrics(self):
        """Flush metrics buffer"""
        with self._lock:
            if not self._buffer:
                return
            
            # Log metrics summary
            buffer_copy = self._buffer.copy()
            self._buffer.clear()
        
        # This is where you would send metrics to external systems
        # For now, we'll just log a summary
        if buffer_copy:
            counter_metrics = len([m for m in buffer_copy if m.type == MetricType.COUNTER])
            gauge_metrics = len([m for m in buffer_copy if m.type == MetricType.GAUGE])
            histogram_metrics = len([m for m in buffer_copy if m.type == MetricType.HISTOGRAM])
            
            logger.debug(f"Flushed {len(buffer_copy)} metrics: "
                        f"{counter_metrics} counters, {gauge_metrics} gauges, "
                        f"{histogram_metrics} histograms")


class PerformanceMonitor:
    """Performance monitoring for operations"""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics_collector = metrics_collector
        self._operation_metrics: Dict[str, PerformanceMetrics] = {}
        self._lock = threading.RLock()
    
    @asynccontextmanager
    async def measure(self, operation_name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for measuring operation performance"""
        start_time = time.time()
        success = False
        error_type = None
        
        try:
            yield
            success = True
        except Exception as e:
            error_type = type(e).__name__
            raise
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Record performance metrics
            self._record_measurement(operation_name, duration_ms, success, error_type)
            
            # Record to metrics collector if available
            if self.metrics_collector:
                self.metrics_collector.observe(
                    f"operation_duration_ms",
                    duration_ms,
                    tags={**(tags or {}), 'operation': operation_name, 'success': str(success)}
                )
                
                if success:
                    self.metrics_collector.increment(
                        "operation_success_total",
                        tags={**(tags or {}), 'operation': operation_name}
                    )
                else:
                    self.metrics_collector.increment(
                        "operation_error_total",
                        tags={**(tags or {}), 'operation': operation_name, 'error_type': error_type}
                    )
    
    def _record_measurement(self, operation_name: str, duration_ms: float, success: bool, error_type: Optional[str]):
        """Record performance measurement"""
        with self._lock:
            if operation_name not in self._operation_metrics:
                self._operation_metrics[operation_name] = PerformanceMetrics(operation_name)
            
            self._operation_metrics[operation_name].add_measurement(duration_ms, success, error_type)
    
    def get_operation_metrics(self, operation_name: str) -> Optional[PerformanceMetrics]:
        """Get metrics for specific operation"""
        return self._operation_metrics.get(operation_name)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all operation metrics"""
        with self._lock:
            return {
                name: metrics.to_dict()
                for name, metrics in self._operation_metrics.items()
            }


class AlertManager:
    """Alert management system with configurable rules"""
    
    def __init__(self):
        self._rules: List[AlertRule] = []
        self._alert_handlers: List[Callable[[str, AlertSeverity, str], None]] = []
        self._lock = threading.RLock()
        
        # Alert statistics
        self._alert_stats = {
            'total_alerts': 0,
            'alerts_by_severity': defaultdict(int),
            'alerts_by_rule': defaultdict(int)
        }
    
    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        with self._lock:
            self._rules.append(rule)
        logger.info(f"Added alert rule: {rule.name} (severity: {rule.severity.value})")
    
    def add_handler(self, handler: Callable[[str, AlertSeverity, str], None]):
        """Add alert handler"""
        self._alert_handlers.append(handler)
        logger.info(f"Added alert handler: {handler.__name__}")
    
    def check_alerts(self, monitoring_system: 'MonitoringSystem'):
        """Check all alert rules and trigger alerts if needed"""
        with self._lock:
            for rule in self._rules:
                try:
                    if rule.should_trigger(monitoring_system):
                        message = rule.trigger(monitoring_system)
                        self._send_alert(rule.name, rule.severity, message)
                        
                        # Update statistics
                        self._alert_stats['total_alerts'] += 1
                        self._alert_stats['alerts_by_severity'][rule.severity.value] += 1
                        self._alert_stats['alerts_by_rule'][rule.name] += 1
                        
                except Exception as e:
                    logger.error(f"Error checking alert rule {rule.name}: {e}")
    
    def _send_alert(self, rule_name: str, severity: AlertSeverity, message: str):
        """Send alert to all handlers"""
        logger.warning(f"ALERT [{severity.value.upper()}] {rule_name}: {message}")
        
        for handler in self._alert_handlers:
            try:
                handler(rule_name, severity, message)
            except Exception as e:
                logger.error(f"Error in alert handler {handler.__name__}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        return {
            **self._alert_stats,
            'rules_count': len(self._rules),
            'handlers_count': len(self._alert_handlers)
        }


class MonitoringSystem:
    """Central monitoring system that coordinates all monitoring components"""
    
    def __init__(self, name: str = "wildosnode_grpc"):
        self.name = name
        
        # Initialize components
        self.logger = StructuredLogger(f"{name}_monitoring")
        self.metrics = MetricsCollector()
        self.performance = PerformanceMonitor(self.metrics)
        self.alerts = AlertManager()
        
        # System state
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
        
        # Default alert rules
        self._setup_default_alert_rules()
        
        logger.info(f"Monitoring system '{name}' initialized")
    
    async def start(self):
        """Start monitoring system"""
        if self._running:
            return
        
        self._running = True
        await self.metrics.start()
        
        # Start periodic alert checking
        self._check_task = asyncio.create_task(self._periodic_alert_check())
        
        self.logger.info("Monitoring system started")
    
    async def stop(self):
        """Stop monitoring system"""
        self._running = False
        
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        
        await self.metrics.stop()
        self.logger.info("Monitoring system stopped")
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules for common issues"""
        
        # High error rate alert
        self.alerts.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda ms: self._get_error_rate() > 10.0,  # >10% error rate
            severity=AlertSeverity.WARNING,
            message_template="High error rate detected: {error_rate:.1f}% in gRPC operations",
            cooldown_seconds=300
        ))
        
        # Connection pool exhausted
        self.alerts.add_rule(AlertRule(
            name="connection_pool_exhausted",
            condition=lambda ms: ms.metrics.get_gauge("connection_pool_available", {"type": "grpc"}) == 0,
            severity=AlertSeverity.ERROR,
            message_template="gRPC connection pool exhausted - no available connections",
            cooldown_seconds=120
        ))
        
        # High response time
        self.alerts.add_rule(AlertRule(
            name="high_response_time",
            condition=lambda ms: self._get_avg_response_time() > 5000,  # >5 seconds
            severity=AlertSeverity.WARNING,
            message_template="High average response time: {avg_time:.0f}ms",
            cooldown_seconds=300
        ))
        
        # Circuit breaker open
        self.alerts.add_rule(AlertRule(
            name="circuit_breaker_open",
            condition=lambda ms: ms.metrics.get_counter("circuit_breaker_open_total") > 0,
            severity=AlertSeverity.ERROR,
            message_template="Circuit breaker(s) opened due to service failures",
            cooldown_seconds=180
        ))
    
    def _get_error_rate(self) -> float:
        """Calculate current error rate"""
        total_ops = self.metrics.get_counter("operation_total")
        error_ops = self.metrics.get_counter("operation_error_total")
        
        if total_ops == 0:
            return 0.0
        
        return (error_ops / total_ops) * 100
    
    def _get_avg_response_time(self) -> float:
        """Get average response time across all operations"""
        histogram_stats = self.metrics.get_histogram_stats("operation_duration_ms")
        return histogram_stats.get('mean', 0.0)
    
    async def _periodic_alert_check(self):
        """Periodic alert checking"""
        while self._running:
            try:
                self.alerts.check_alerts(self)
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error("Error in periodic alert check", error=e)
                await asyncio.sleep(30)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        error_rate = self._get_error_rate()
        avg_response_time = self._get_avg_response_time()
        
        # Determine health status
        if error_rate > 25 or avg_response_time > 10000:
            health = "unhealthy"
        elif error_rate > 10 or avg_response_time > 5000:
            health = "degraded"
        else:
            health = "healthy"
        
        return {
            'status': health,
            'error_rate_percent': error_rate,
            'avg_response_time_ms': avg_response_time,
            'metrics': self.metrics.get_all_metrics(),
            'performance': self.performance.get_all_metrics(),
            'alerts': self.alerts.get_stats(),
            'timestamp': time.time()
        }


# Global monitoring instance
_global_monitoring: Optional[MonitoringSystem] = None


def get_monitoring() -> MonitoringSystem:
    """Get global monitoring system instance"""
    global _global_monitoring
    if _global_monitoring is None:
        _global_monitoring = MonitoringSystem()
        # Start the monitoring system asynchronously
        asyncio.create_task(_global_monitoring.start())
    return _global_monitoring


# Decorators for monitoring
def monitor_performance(operation_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
    """Decorator for monitoring operation performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            monitoring = get_monitoring()
            
            async with monitoring.performance.measure(op_name, tags):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_errors(logger_name: Optional[str] = None):
    """Decorator for automatic error logging"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitoring = get_monitoring()
            op_logger = monitoring.logger if not logger_name else StructuredLogger(logger_name)
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                op_logger.error(f"Error in {func.__name__}", error=e, operation=func.__name__)
                raise
        
        return wrapper
    return decorator


# Integration interfaces for external systems
class ErrorAggregator:
    """Aggregates and exports error data for dashboard integration"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_rates: Dict[str, float] = {}
        self.critical_errors: List[Dict[str, Any]] = []
        self.system_health: Dict[str, Any] = {}
        self._last_aggregation = time.time()
        
    def add_error(self, error: WildosNodeBaseError, component: str):
        """Add error to aggregation for dashboard reporting"""
        error_key = f"{component}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Track critical errors separately
        if error.severity.value == 'critical':
            self.critical_errors.append({
                'timestamp': error.context.timestamp if error.context else time.time(),
                'error_type': type(error).__name__,
                'component': component,
                'message': str(error),
                'node_id': error.context.node_id if error.context else None,
                'operation': error.context.operation if error.context else None
            })
            
            # Keep only last 100 critical errors
            if len(self.critical_errors) > 100:
                self.critical_errors = self.critical_errors[-100:]
    
    def calculate_error_rates(self, time_window: float = 300.0) -> Dict[str, float]:
        """Calculate error rates over time window (default 5 minutes)"""
        current_time = time.time()
        
        # Filter recent critical errors
        recent_errors = [
            err for err in self.critical_errors 
            if current_time - err['timestamp'] <= time_window
        ]
        
        # Calculate rates by component
        component_rates = {}
        for error in recent_errors:
            component = error['component']
            if component not in component_rates:
                component_rates[component] = 0
            component_rates[component] += 1
        
        # Convert to rate per minute
        for component in component_rates:
            component_rates[component] = (component_rates[component] / time_window) * 60
        
        self.error_rates = component_rates
        return component_rates
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get aggregated data for dashboard display"""
        self.calculate_error_rates()
        
        return {
            'error_counts': self.error_counts.copy(),
            'error_rates_per_minute': self.error_rates.copy(),
            'critical_errors_recent': self.critical_errors[-10:],  # Last 10 critical errors
            'total_errors': sum(self.error_counts.values()),
            'components_with_errors': list(set([key.split(':')[0] for key in self.error_counts.keys()])),
            'last_updated': time.time(),
            'system_health': self.system_health.copy()
        }
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format for scraping"""
        metrics = []
        
        # Error counts
        for error_key, count in self.error_counts.items():
            component, error_type = error_key.split(':', 1)
            metrics.append(
                f'wildos_errors_total{{component="{component}",error_type="{error_type}"}} {count}'
            )
        
        # Error rates
        for component, rate in self.error_rates.items():
            metrics.append(
                f'wildos_error_rate_per_minute{{component="{component}"}} {rate:.2f}'
            )
        
        # Critical error count
        critical_count = len(self.critical_errors)
        metrics.append(f'wildos_critical_errors_total {critical_count}')
        
        # System health indicators
        for metric, value in self.system_health.items():
            if isinstance(value, (int, float)):
                metrics.append(f'wildos_system_{metric} {value}')
        
        return '\n'.join(metrics)
    
    def update_system_health(self, component: str, health_data: Dict[str, Any]):
        """Update system health information"""
        self.system_health[component] = {
            **health_data,
            'last_updated': time.time()
        }

class StatusReporter:
    """Reports system status to parent systems"""
    
    def __init__(self):
        self.component_statuses: Dict[str, Dict[str, Any]] = {}
        self.overall_status = 'healthy'
        self.status_history: List[Dict[str, Any]] = []
        
    def update_component_status(self, component: str, status: str, details: Dict[str, Any] = None):
        """Update status for a specific component"""
        self.component_statuses[component] = {
            'status': status,  # 'healthy', 'degraded', 'critical', 'down'
            'details': details or {},
            'last_updated': time.time()
        }
        
        # Update overall status
        self._calculate_overall_status()
        
        # Add to history
        self.status_history.append({
            'timestamp': time.time(),
            'component': component,
            'status': status,
            'details': details
        })
        
        # Keep only last 1000 status changes
        if len(self.status_history) > 1000:
            self.status_history = self.status_history[-1000:]
    
    def _calculate_overall_status(self):
        """Calculate overall system status based on component statuses"""
        if not self.component_statuses:
            self.overall_status = 'unknown'
            return
        
        statuses = [comp['status'] for comp in self.component_statuses.values()]
        
        if 'down' in statuses:
            self.overall_status = 'down'
        elif 'critical' in statuses:
            self.overall_status = 'critical'
        elif 'degraded' in statuses:
            self.overall_status = 'degraded'
        else:
            self.overall_status = 'healthy'
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            'overall_status': self.overall_status,
            'components': self.component_statuses.copy(),
            'status_summary': {
                'healthy': len([s for s in self.component_statuses.values() if s['status'] == 'healthy']),
                'degraded': len([s for s in self.component_statuses.values() if s['status'] == 'degraded']),
                'critical': len([s for s in self.component_statuses.values() if s['status'] == 'critical']),
                'down': len([s for s in self.component_statuses.values() if s['status'] == 'down'])
            },
            'recent_changes': self.status_history[-20:],  # Last 20 status changes
            'timestamp': time.time()
        }
    
    def export_json_status(self) -> str:
        """Export status as JSON for API consumption"""
        return json.dumps(self.get_status_report(), indent=2)

class MetricsExporter:
    """Exports metrics to external monitoring systems"""
    
    def __init__(self):
        self.metrics_cache: Dict[str, Any] = {}
        self.export_formats = ['prometheus', 'json', 'csv']
        
    def add_metrics(self, source: str, metrics: Dict[str, Any]):
        """Add metrics from a source"""
        self.metrics_cache[source] = {
            'metrics': metrics,
            'timestamp': time.time()
        }
    
    def export_all_metrics(self, format: str = 'json') -> str:
        """Export all cached metrics in specified format"""
        if format == 'prometheus':
            return self._export_prometheus()
        elif format == 'json':
            return self._export_json()
        elif format == 'csv':
            return self._export_csv()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_prometheus(self) -> str:
        """Export in Prometheus format"""
        lines = []
        for source, data in self.metrics_cache.items():
            for metric_name, value in data['metrics'].items():
                if isinstance(value, (int, float)):
                    lines.append(f'wildos_{source}_{metric_name} {value}')
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (int, float)):
                            lines.append(f'wildos_{source}_{metric_name}_{sub_key} {sub_value}')
        return '\n'.join(lines)
    
    def _export_json(self) -> str:
        """Export in JSON format"""
        return json.dumps({
            'timestamp': time.time(),
            'sources': self.metrics_cache
        }, indent=2)
    
    def _export_csv(self) -> str:
        """Export in CSV format"""
        lines = ['source,metric_name,value,timestamp']
        for source, data in self.metrics_cache.items():
            timestamp = data['timestamp']
            for metric_name, value in data['metrics'].items():
                if isinstance(value, (int, float)):
                    lines.append(f'{source},{metric_name},{value},{timestamp}')
        return '\n'.join(lines)

# Global integration instances
_error_aggregator: Optional[ErrorAggregator] = None
_status_reporter: Optional[StatusReporter] = None
_metrics_exporter: Optional[MetricsExporter] = None

def get_error_aggregator() -> ErrorAggregator:
    """Get global error aggregator instance"""
    global _error_aggregator
    if _error_aggregator is None:
        _error_aggregator = ErrorAggregator()
    return _error_aggregator

def get_status_reporter() -> StatusReporter:
    """Get global status reporter instance"""
    global _status_reporter
    if _status_reporter is None:
        _status_reporter = StatusReporter()
    return _status_reporter

def get_metrics_exporter() -> MetricsExporter:
    """Get global metrics exporter instance"""
    global _metrics_exporter
    if _metrics_exporter is None:
        _metrics_exporter = MetricsExporter()
    return _metrics_exporter

# Enhanced monitoring system integrations
def integrate_error_aggregation(monitoring_system: MonitoringSystem):
    """Integrate error aggregation with monitoring system"""
    error_aggregator = get_error_aggregator()
    status_reporter = get_status_reporter()
    
    # Add alert rule for high error rates
    def high_error_rate_condition(ms: MonitoringSystem) -> bool:
        rates = error_aggregator.calculate_error_rates()
        return any(rate > 10 for rate in rates.values())  # More than 10 errors/minute
    
    monitoring_system.alerts.add_rule(AlertRule(
        name="high_error_rate",
        condition=high_error_rate_condition,
        severity=AlertSeverity.WARNING,
        message_template="High error rate detected: {error_rate:.1f}% at {timestamp}"
    ))
    
    return error_aggregator, status_reporter

def create_metrics_export_endpoint():
    """Create endpoint data for metrics export"""
    exporter = get_metrics_exporter()
    monitoring = get_monitoring()
    
    # Add current monitoring metrics
    exporter.add_metrics('monitoring_system', monitoring.get_health_status())
    
    return {
        'prometheus': lambda: exporter.export_all_metrics('prometheus'),
        'json': lambda: exporter.export_all_metrics('json'),
        'csv': lambda: exporter.export_all_metrics('csv'),
        'health': lambda: get_status_reporter().export_json_status(),
        'errors': lambda: get_error_aggregator().export_prometheus_metrics()
    }

# Cleanup function
async def cleanup_monitoring():
    """Cleanup global monitoring system"""
    global _global_monitoring, _error_aggregator, _status_reporter, _metrics_exporter
    if _global_monitoring:
        await _global_monitoring.stop()
        _global_monitoring = None
    
    # Reset integration instances
    _error_aggregator = None
    _status_reporter = None
    _metrics_exporter = None