from enum import Enum
from typing import List, Optional, Dict

from pydantic import ConfigDict, BaseModel, Field, validator
from app.config.env import NODE_GRPC_PORT


class BackendConfigFormat(Enum):
    PLAIN = 0
    JSON = 1
    YAML = 2


class BackendConfig(BaseModel):
    config: str
    format: BackendConfigFormat


class BackendStats(BaseModel):
    running: bool


class Backend(BaseModel):
    name: str
    backend_type: str
    version: str | None
    running: bool


class NodeStatus(str, Enum):
    healthy = "healthy"
    unhealthy = "unhealthy"
    disabled = "disabled"


class NodeConnectionBackend(str, Enum):
    grpclib = "grpclib"


class NodeSettings(BaseModel):
    min_node_version: str = "v0.2.0"
    certificate: str


class Node(BaseModel):
    id: int | None = Field(None)
    name: str
    address: str
    port: int = Field(default=NODE_GRPC_PORT)
    connection_backend: NodeConnectionBackend = Field(
        default=NodeConnectionBackend.grpclib
    )
    usage_coefficient: float = Field(ge=0, default=1.0)
    model_config = ConfigDict(from_attributes=True)


class NodeCreate(Node):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "DE node",
                "address": "192.168.1.1",
                "port": NODE_GRPC_PORT,
                "usage_coefficient": 1,
            }
        }
    )


class NodeModify(BaseModel):
    name: str | None = Field(None)
    address: str | None = Field(None)
    port: int | None = Field(None)
    connection_backend: NodeConnectionBackend | None = Field(None)
    status: NodeStatus | None = Field(None)
    usage_coefficient: float | None = Field(None, ge=0)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "DE node",
                "address": "192.168.1.1",
                "port": NODE_GRPC_PORT,
                "status": "disabled",
                "usage_coefficient": 1.0,
            }
        }
    )


class NodeResponse(Node):
    xray_version: str | None = None
    status: NodeStatus
    message: str | None = None
    model_config = ConfigDict(from_attributes=True)
    inbound_ids: list[int] | None = None
    backends: list[Backend]


class NodeUsageResponse(BaseModel):
    node_id: int | None = None
    node_name: str
    uplink: int
    downlink: int


class NodesUsageResponse(BaseModel):
    usages: list[NodeUsageResponse]


# Host System Models
class CPUMetrics(BaseModel):
    usage: float
    load_average: List[float]  # 1, 5, 15 min averages

class MemoryMetrics(BaseModel):
    total: str
    used: str
    available: str
    usage_percent: float

class DiskPartition(BaseModel):
    device: str
    mount_point: str
    total: str
    used: str
    available: str
    usage_percent: float

class DiskMetrics(BaseModel):
    root_usage_percent: float
    partitions: List[DiskPartition]

class NetworkInterface(BaseModel):
    name: str
    ip: str
    rx_bytes: str
    tx_bytes: str
    speed: str

class NetworkMetrics(BaseModel):
    interfaces: List[NetworkInterface]

class UptimeMetrics(BaseModel):
    seconds: int
    formatted: str

class PortInfo(BaseModel):
    number: int
    protocol: str
    service: Optional[str] = None

class HostSystemMetrics(BaseModel):
    cpu: CPUMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    network: NetworkMetrics
    uptime: UptimeMetrics
    open_ports: List[PortInfo]

# Container Models
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

class ContainerLog(BaseModel):
    timestamp: str
    level: LogLevel
    message: str
    source: Optional[str] = None

class ContainerFile(BaseModel):
    name: str
    type: str  # file, directory
    size: Optional[str] = None
    modified: Optional[str] = None
    permissions: Optional[str] = None

class PortActionRequest(BaseModel):
    port: int = Field(..., ge=1, le=65535, description="Port number (1-65535)")
    protocol: str = Field(default="tcp", pattern="^(tcp|udp)$")

class PortActionResponse(BaseModel):
    success: bool
    message: str

# Container operation response models
class ContainerRestartResponse(BaseModel):
    success: bool
    message: str

# Batch backend stats response model
class AllBackendsStatsResponse(BaseModel):
    backends: Dict[str, BackendStats]
    node_id: int
    timestamp: str

# Peak Events Monitoring Models
class PeakLevel(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class PeakCategory(str, Enum):
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"
    BACKEND = "BACKEND"

class PeakEvent(BaseModel):
    """Peak event monitoring data - aligned with protobuf schema"""
    node_id: int
    category: PeakCategory
    metric: str  # Specific metric name that triggered the peak
    level: PeakLevel
    value: float   # Current metric value
    threshold: float  # Threshold that was exceeded
    dedupe_key: str  # Deduplication key for event grouping
    context_json: str = "{}"  # Additional context as JSON string
    started_at_ms: int  # Event start timestamp in milliseconds
    resolved_at_ms: Optional[int] = None  # Event resolution timestamp (None for ongoing)
    seq: int = 0  # Sequence number for event ordering


class PeakEventCreate(BaseModel):
    """Model for creating peak events via API"""
    category: PeakCategory
    metric: str
    level: PeakLevel  
    value: float
    threshold: float
    dedupe_key: str
    context_json: Optional[Dict] = {}
    started_at_ms: int
    resolved_at_ms: Optional[int] = None
    seq: int = 0
