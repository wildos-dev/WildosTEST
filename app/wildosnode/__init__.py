"""stores nodes and provides entities to communicate with the nodes"""

from typing import Dict

from . import operations
from .base import WildosNodeBase
# WildosNodeGRPCLIB импортируется лениво для избежания проблем с app.* зависимостями

nodes: Dict[int, WildosNodeBase] = {}


def __getattr__(name):
    if name == "WildosNodeGRPCLIB":
        from .grpc_client import WildosNodeGRPCLIB
        return WildosNodeGRPCLIB
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "nodes",
    "operations",
    "WildosNodeGRPCLIB",
    "WildosNodeBase",
]
