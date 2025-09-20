"""
Менеджер последовательности событий для агента мониторинга пиков.
Обеспечивает персистентность sequence counter между перезапусками контейнера.
"""

import os
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

class PeakSequenceManager:
    """
    Менеджер для сохранения монотонной последовательности событий пиков
    между перезапусками контейнера узла.
    """
    
    def __init__(self, node_id: int, seq_file_path: str = "/tmp/peak_seq.txt"):
        self.node_id = node_id
        self.seq_file_path = seq_file_path
        self._current_seq = 0
        self._lock = threading.Lock()
        self._load_sequence()
    
    def _load_sequence(self):
        """Загрузить последнюю последовательность из файла"""
        try:
            if os.path.exists(self.seq_file_path):
                with open(self.seq_file_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self._current_seq = int(content)
                        logger.info(f"Loaded peak sequence: {self._current_seq}")
                    else:
                        self._current_seq = 0
            else:
                self._current_seq = 0
                logger.info("No existing peak sequence file, starting from 0")
        except Exception as e:
            logger.warning(f"Failed to load peak sequence: {e}, starting from 0")
            self._current_seq = 0
    
    def _save_sequence(self):
        """Сохранить текущую последовательность в файл"""
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(self.seq_file_path), exist_ok=True)
            
            with open(self.seq_file_path, 'w') as f:
                f.write(str(self._current_seq))
                f.flush()
                os.fsync(f.fileno())  # Принудительная запись на диск
        except Exception as e:
            logger.error(f"Failed to save peak sequence: {e}")
    
    def get_next_sequence(self) -> int:
        """Получить следующий номер последовательности"""
        with self._lock:
            self._current_seq += 1
            self._save_sequence()
            return self._current_seq
    
    def get_current_sequence(self) -> int:
        """Получить текущий номер последовательности"""
        with self._lock:
            return self._current_seq

# Глобальный экземпляр менеджера
_seq_manager: Optional[PeakSequenceManager] = None

def get_sequence_manager(node_id: int) -> PeakSequenceManager:
    """Получить глобальный экземпляр менеджера последовательности"""
    global _seq_manager
    if _seq_manager is None:
        _seq_manager = PeakSequenceManager(node_id)
    return _seq_manager