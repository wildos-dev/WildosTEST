"""
Peak monitoring agent for in-container resource tracking with intelligent deduplication.
Runs inside Docker container and streams peak events to panel via gRPC.
"""

import asyncio
import logging
import time
import json
import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime, timezone

from .peak_seq_manager import get_sequence_manager

# Импорты protobuf классов из node service
def _get_protobuf_classes():
    """Импорт protobuf классов из node service"""
    from ..service.service_pb2 import PeakEvent, PeakCategory, PeakLevel
    return PeakEvent, PeakCategory, PeakLevel

logger = logging.getLogger(__name__)

class PeakState(Enum):
    """FSM состояния для отслеживания пиков"""
    IDLE = "idle"
    RISING = "rising" 
    PEAK = "peak"
    COOLING = "cooling"

@dataclass
class ThresholdConfig:
    """Конфигурация порогов для мониторинга"""
    cpu_warning: float = 75.0
    cpu_critical: float = 90.0
    memory_warning: float = 80.0
    memory_critical: float = 95.0
    hysteresis_percent: float = 5.0  # Гистерезис для предотвращения флаппинга
    min_duration_seconds: int = 30   # Минимальная длительность пика
    cool_down_cycles: int = 2        # Циклы ожидания ниже порога

@dataclass
class PeakTracker:
    """Трекер состояния для конкретной метрики"""
    state: PeakState = PeakState.IDLE
    start_time: Optional[float] = None
    peak_value: float = 0.0
    threshold: float = 0.0
    level: str = "WARNING"
    context_snapshot: Dict[str, Any] = None
    cool_down_counter: int = 0
    last_seq: int = 0

class InContainerPeakMonitor:
    """
    Агент мониторинга пиковых моментов для работы внутри Docker контейнера узла.
    Реализует FSM с умной дедупликацией и стримингом событий на панель.
    """
    
    def __init__(self, node_id: int, config: ThresholdConfig = None):
        self.node_id = node_id
        self.config = config or ThresholdConfig()
        self.trackers: Dict[str, PeakTracker] = {}
        self.seq_manager = get_sequence_manager(node_id)
        self.is_running = False
        self.metrics_buffer = []
        
        # Очередь событий для стриминга
        self.peak_events_queue = asyncio.Queue()
        
    def _get_system_metrics(self) -> Optional[Dict[str, float]]:
        """
        Получить текущие системные метрики.
        Возвращает None если psutil недоступен (отключает мониторинг).
        """
        try:
            import psutil
            
            # CPU метрики
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg()
            
            # Memory метрики  
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk метрики для корневого раздела
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network метрики (упрощенно)
            net_io = psutil.net_io_counters()
            
            return {
                'cpu_usage': cpu_percent,
                'load_1min': load_avg[0] if load_avg else 0,
                'memory_percent': memory_percent,
                'memory_used': memory.used,
                'memory_total': memory.total,
                'disk_percent': disk_percent,
                'disk_used': disk.used,
                'disk_total': disk.total,
                'network_rx_bytes': net_io.bytes_recv,
                'network_tx_bytes': net_io.bytes_sent,
                'timestamp': time.time()
            }
        except ImportError:
            logger.error("psutil not available - peak monitoring disabled")
            return None
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    def _get_backend_context(self) -> Dict[str, Any]:
        """
        Получить контекст состояния backend'ов для диагностики.
        Здесь должно быть обращение к локальным API backend'ов.
        """
        # Упрощенная реализация - в реальности здесь обращение к Xray API
        return {
            'active_users': 0,  # Количество активных пользователей
            'backend_status': 'running',
            'connection_count': 0,
            'traffic_rate_mbps': 0.0
        }
    
    def _create_dedupe_key(self, category: str, metric: str, context_id: str = "") -> str:
        """Создать ключ дедупликации для группировки событий"""
        key_string = f"{self.node_id}:{category}:{metric}:{context_id}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _check_thresholds(self, metrics: Dict[str, float]) -> list:
        """Проверить пороги и вернуть список превышений"""
        violations = []
        
        # CPU проверки
        cpu_usage = metrics.get('cpu_usage', 0)
        if cpu_usage >= self.config.cpu_critical:
            violations.append(('CPU', 'cpu_usage', cpu_usage, self.config.cpu_critical, 'CRITICAL'))
        elif cpu_usage >= self.config.cpu_warning:
            violations.append(('CPU', 'cpu_usage', cpu_usage, self.config.cpu_warning, 'WARNING'))
            
        # Memory проверки
        memory_percent = metrics.get('memory_percent', 0)
        if memory_percent >= self.config.memory_critical:
            violations.append(('MEMORY', 'memory_percent', memory_percent, self.config.memory_critical, 'CRITICAL'))
        elif memory_percent >= self.config.memory_warning:
            violations.append(('MEMORY', 'memory_percent', memory_percent, self.config.memory_warning, 'WARNING'))
            
        return violations
    
    def _process_violation(self, category: str, metric: str, value: float, 
                          threshold: float, level: str, context: Dict[str, Any]) -> Optional[Dict]:
        """Обработать нарушение порога с помощью FSM"""
        
        tracker_key = f"{category}:{metric}"
        tracker = self.trackers.get(tracker_key)
        
        if not tracker:
            tracker = PeakTracker()
            self.trackers[tracker_key] = tracker
            
        current_time = time.time()
        
        # FSM логика
        if tracker.state == PeakState.IDLE:
            # Начало пика
            tracker.state = PeakState.RISING
            tracker.start_time = current_time
            tracker.peak_value = value
            tracker.threshold = threshold
            tracker.level = level
            tracker.context_snapshot = context.copy()
            tracker.cool_down_counter = 0
            
            return self._create_peak_event(category, metric, value, threshold, level, 
                                         context, current_time, None, "start")
                                         
        elif tracker.state in [PeakState.RISING, PeakState.PEAK]:
            # Обновление максимального значения в рамках пика
            if value > tracker.peak_value:
                tracker.peak_value = value
                tracker.threshold = max(tracker.threshold, threshold)
                if level == 'CRITICAL' and tracker.level == 'WARNING':
                    tracker.level = level  # Повышение уровня критичности
            
            tracker.state = PeakState.PEAK
            tracker.cool_down_counter = 0
            # Не создаем новое событие - это тот же пик
            return None
            
        elif tracker.state == PeakState.COOLING:
            # Возврат к пику
            tracker.state = PeakState.PEAK
            tracker.cool_down_counter = 0
            if value > tracker.peak_value:
                tracker.peak_value = value
            return None
            
        return None
    
    def _process_no_violation(self, category: str, metric: str, value: float) -> Optional[Dict]:
        """Обработать отсутствие нарушений - возможное завершение пика"""
        
        tracker_key = f"{category}:{metric}"
        tracker = self.trackers.get(tracker_key)
        
        if not tracker or tracker.state == PeakState.IDLE:
            return None
            
        # Проверка гистерезиса
        hysteresis_threshold = tracker.threshold * (1 - self.config.hysteresis_percent / 100)
        
        if value < hysteresis_threshold:
            if tracker.state == PeakState.PEAK:
                tracker.state = PeakState.COOLING
                tracker.cool_down_counter = 1
            elif tracker.state == PeakState.COOLING:
                tracker.cool_down_counter += 1
                
                # Завершение пика после cool_down_cycles
                if tracker.cool_down_counter >= self.config.cool_down_cycles:
                    current_time = time.time()
                    duration = current_time - tracker.start_time
                    
                    # Проверка минимальной длительности
                    if duration >= self.config.min_duration_seconds:
                        event = self._create_peak_event(
                            category, metric, tracker.peak_value, tracker.threshold,
                            tracker.level, tracker.context_snapshot, 
                            tracker.start_time, current_time, "resolve"
                        )
                        
                        # Сброс трекера
                        tracker.state = PeakState.IDLE
                        tracker.start_time = None
                        tracker.cool_down_counter = 0
                        
                        return event
        else:
            # Значение все еще выше гистерезиса
            if tracker.state == PeakState.COOLING:
                tracker.state = PeakState.PEAK
                tracker.cool_down_counter = 0
                
        return None
    
    def _create_peak_event(self, category: str, metric: str, value: float, 
                          threshold: float, level: str, context: Dict[str, Any],
                          started_at: float, resolved_at: Optional[float],
                          event_type: str):
        """Создать событие пика для отправки на панель"""
        
        seq = self.seq_manager.get_next_sequence()
        dedupe_key = self._create_dedupe_key(category, metric)
        
        # Конвертация времени в миллисекунды
        started_at_ms = int(started_at * 1000)
        resolved_at_ms = int(resolved_at * 1000) if resolved_at else None
        
        # Создание protobuf события
        PeakEvent, PeakCategory, PeakLevel = _get_protobuf_classes()
        
        # Конвертация строковых enum в protobuf enum
        pb_category = getattr(PeakCategory, category)
        pb_level = getattr(PeakLevel, level)
        
        # Создание protobuf сообщения
        event = PeakEvent(
            node_id=self.node_id,
            category=pb_category,
            metric=metric,
            value=value,
            threshold=threshold,
            level=pb_level,
            dedupe_key=dedupe_key,
            context_json=json.dumps(context),
            started_at_ms=started_at_ms,
            seq=seq
        )
        
        if resolved_at_ms:
            event.resolved_at_ms = resolved_at_ms
        
        logger.info(f"Peak {event_type}: {category}/{metric} = {value:.1f} (threshold: {threshold:.1f}, level: {level})")
        
        return event
    
    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        
        logger.info(f"Starting peak monitoring for node {self.node_id}")
        
        while self.is_running:
            try:
                # Получение метрик
                metrics = self._get_system_metrics()
                if metrics is None:
                    # psutil недоступен - отключаем мониторинг
                    logger.warning("System metrics unavailable, stopping monitoring")
                    break
                    
                context = self._get_backend_context()
                
                # Проверка порогов
                violations = self._check_thresholds(metrics)
                
                # Обработка нарушений  
                for category, metric, value, threshold, level in violations:
                    event = self._process_violation(category, metric, value, threshold, level, {
                        **context,
                        'metrics_snapshot': metrics
                    })
                    if event:
                        await self.peak_events_queue.put(event)
                
                # Обработка завершений пиков для метрик без нарушений
                monitored_metrics = [
                    ('CPU', 'cpu_usage', metrics.get('cpu_usage', 0)),
                    ('MEMORY', 'memory_percent', metrics.get('memory_percent', 0))
                ]
                
                active_violations = {(cat, metric) for cat, metric, _, _, _ in violations}
                
                for category, metric, value in monitored_metrics:
                    if (category, metric) not in active_violations:
                        event = self._process_no_violation(category, metric, value)
                        if event:
                            await self.peak_events_queue.put(event)
                
                # Пауза между проверками
                await asyncio.sleep(5)  # 5 секунд между проверками
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Увеличенная пауза при ошибке
    
    async def get_peak_events_stream(self):
        """Генератор для стриминга protobuf событий пиков"""
        while True:
            try:
                event = await asyncio.wait_for(
                    self.peak_events_queue.get(), 
                    timeout=30  # Heartbeat каждые 30 секунд
                )
                yield event
            except asyncio.TimeoutError:
                # Timeout - цикл продолжается без отправки событий
                # gRPC keepalive обрабатывает поддержание соединения
                continue
    
    def start(self):
        """Запустить агент мониторинга"""
        if self.is_running:
            logger.warning("Peak monitor already running")
            return
            
        self.is_running = True
        return asyncio.create_task(self._monitoring_loop())
    
    def stop(self):
        """Остановить агент мониторинга"""
        self.is_running = False
        logger.info("Peak monitoring stopped")

# Глобальный экземпляр агента
_monitor_instance: Optional[InContainerPeakMonitor] = None

def get_peak_monitor(node_id: int) -> InContainerPeakMonitor:
    """Получить глобальный экземпляр агента мониторинга"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = InContainerPeakMonitor(node_id)
    return _monitor_instance