"""A module to store wildosnode data"""

from .base import BaseStorage
from .memory import MemoryStorage

__all__ = ["BaseStorage", "MemoryStorage"]
