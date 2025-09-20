from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConfigFormat(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PLAIN: _ClassVar[ConfigFormat]
    JSON: _ClassVar[ConfigFormat]
    YAML: _ClassVar[ConfigFormat]

class PeakLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WARNING: _ClassVar[PeakLevel]
    CRITICAL: _ClassVar[PeakLevel]

class PeakCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CPU: _ClassVar[PeakCategory]
    MEMORY: _ClassVar[PeakCategory]
    DISK: _ClassVar[PeakCategory]
    NETWORK: _ClassVar[PeakCategory]
    BACKEND: _ClassVar[PeakCategory]
PLAIN: ConfigFormat
JSON: ConfigFormat
YAML: ConfigFormat
WARNING: PeakLevel
CRITICAL: PeakLevel
CPU: PeakCategory
MEMORY: PeakCategory
DISK: PeakCategory
NETWORK: PeakCategory
BACKEND: PeakCategory

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Backend(_message.Message):
    __slots__ = ("name", "type", "version", "inbounds")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    INBOUNDS_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: str
    version: str
    inbounds: _containers.RepeatedCompositeFieldContainer[Inbound]
    def __init__(self, name: _Optional[str] = ..., type: _Optional[str] = ..., version: _Optional[str] = ..., inbounds: _Optional[_Iterable[_Union[Inbound, _Mapping]]] = ...) -> None: ...

class BackendsResponse(_message.Message):
    __slots__ = ("backends",)
    BACKENDS_FIELD_NUMBER: _ClassVar[int]
    backends: _containers.RepeatedCompositeFieldContainer[Backend]
    def __init__(self, backends: _Optional[_Iterable[_Union[Backend, _Mapping]]] = ...) -> None: ...

class Inbound(_message.Message):
    __slots__ = ("tag", "config")
    TAG_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    tag: str
    config: str
    def __init__(self, tag: _Optional[str] = ..., config: _Optional[str] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ("id", "username", "key")
    ID_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    id: int
    username: str
    key: str
    def __init__(self, id: _Optional[int] = ..., username: _Optional[str] = ..., key: _Optional[str] = ...) -> None: ...

class UserData(_message.Message):
    __slots__ = ("user", "inbounds")
    USER_FIELD_NUMBER: _ClassVar[int]
    INBOUNDS_FIELD_NUMBER: _ClassVar[int]
    user: User
    inbounds: _containers.RepeatedCompositeFieldContainer[Inbound]
    def __init__(self, user: _Optional[_Union[User, _Mapping]] = ..., inbounds: _Optional[_Iterable[_Union[Inbound, _Mapping]]] = ...) -> None: ...

class UsersData(_message.Message):
    __slots__ = ("users_data",)
    USERS_DATA_FIELD_NUMBER: _ClassVar[int]
    users_data: _containers.RepeatedCompositeFieldContainer[UserData]
    def __init__(self, users_data: _Optional[_Iterable[_Union[UserData, _Mapping]]] = ...) -> None: ...

class UsersStats(_message.Message):
    __slots__ = ("users_stats",)
    class UserStats(_message.Message):
        __slots__ = ("uid", "usage")
        UID_FIELD_NUMBER: _ClassVar[int]
        USAGE_FIELD_NUMBER: _ClassVar[int]
        uid: int
        usage: int
        def __init__(self, uid: _Optional[int] = ..., usage: _Optional[int] = ...) -> None: ...
    USERS_STATS_FIELD_NUMBER: _ClassVar[int]
    users_stats: _containers.RepeatedCompositeFieldContainer[UsersStats.UserStats]
    def __init__(self, users_stats: _Optional[_Iterable[_Union[UsersStats.UserStats, _Mapping]]] = ...) -> None: ...

class LogLine(_message.Message):
    __slots__ = ("line",)
    LINE_FIELD_NUMBER: _ClassVar[int]
    line: str
    def __init__(self, line: _Optional[str] = ...) -> None: ...

class BackendConfig(_message.Message):
    __slots__ = ("configuration", "config_format")
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FORMAT_FIELD_NUMBER: _ClassVar[int]
    configuration: str
    config_format: ConfigFormat
    def __init__(self, configuration: _Optional[str] = ..., config_format: _Optional[_Union[ConfigFormat, str]] = ...) -> None: ...

class BackendLogsRequest(_message.Message):
    __slots__ = ("backend_name", "include_buffer")
    BACKEND_NAME_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_BUFFER_FIELD_NUMBER: _ClassVar[int]
    backend_name: str
    include_buffer: bool
    def __init__(self, backend_name: _Optional[str] = ..., include_buffer: bool = ...) -> None: ...

class RestartBackendRequest(_message.Message):
    __slots__ = ("backend_name", "config")
    BACKEND_NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    backend_name: str
    config: BackendConfig
    def __init__(self, backend_name: _Optional[str] = ..., config: _Optional[_Union[BackendConfig, _Mapping]] = ...) -> None: ...

class BackendStats(_message.Message):
    __slots__ = ("running",)
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    running: bool
    def __init__(self, running: bool = ...) -> None: ...

class HostSystemMetrics(_message.Message):
    __slots__ = ("cpu_usage", "memory_usage", "memory_total", "disk_usage", "disk_total", "network_interfaces", "uptime_seconds", "load_average_1m", "load_average_5m", "load_average_15m")
    CPU_USAGE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_TOTAL_FIELD_NUMBER: _ClassVar[int]
    DISK_USAGE_FIELD_NUMBER: _ClassVar[int]
    DISK_TOTAL_FIELD_NUMBER: _ClassVar[int]
    NETWORK_INTERFACES_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    LOAD_AVERAGE_1M_FIELD_NUMBER: _ClassVar[int]
    LOAD_AVERAGE_5M_FIELD_NUMBER: _ClassVar[int]
    LOAD_AVERAGE_15M_FIELD_NUMBER: _ClassVar[int]
    cpu_usage: float
    memory_usage: float
    memory_total: float
    disk_usage: float
    disk_total: float
    network_interfaces: _containers.RepeatedCompositeFieldContainer[NetworkInterface]
    uptime_seconds: int
    load_average_1m: float
    load_average_5m: float
    load_average_15m: float
    def __init__(self, cpu_usage: _Optional[float] = ..., memory_usage: _Optional[float] = ..., memory_total: _Optional[float] = ..., disk_usage: _Optional[float] = ..., disk_total: _Optional[float] = ..., network_interfaces: _Optional[_Iterable[_Union[NetworkInterface, _Mapping]]] = ..., uptime_seconds: _Optional[int] = ..., load_average_1m: _Optional[float] = ..., load_average_5m: _Optional[float] = ..., load_average_15m: _Optional[float] = ...) -> None: ...

class NetworkInterface(_message.Message):
    __slots__ = ("name", "bytes_sent", "bytes_received", "packets_sent", "packets_received")
    NAME_FIELD_NUMBER: _ClassVar[int]
    BYTES_SENT_FIELD_NUMBER: _ClassVar[int]
    BYTES_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    PACKETS_SENT_FIELD_NUMBER: _ClassVar[int]
    PACKETS_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    name: str
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    def __init__(self, name: _Optional[str] = ..., bytes_sent: _Optional[int] = ..., bytes_received: _Optional[int] = ..., packets_sent: _Optional[int] = ..., packets_received: _Optional[int] = ...) -> None: ...

class PortActionRequest(_message.Message):
    __slots__ = ("port", "protocol")
    PORT_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    port: int
    protocol: str
    def __init__(self, port: _Optional[int] = ..., protocol: _Optional[str] = ...) -> None: ...

class PortActionResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class ContainerLogsRequest(_message.Message):
    __slots__ = ("tail",)
    TAIL_FIELD_NUMBER: _ClassVar[int]
    tail: int
    def __init__(self, tail: _Optional[int] = ...) -> None: ...

class ContainerLogsResponse(_message.Message):
    __slots__ = ("logs",)
    LOGS_FIELD_NUMBER: _ClassVar[int]
    logs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, logs: _Optional[_Iterable[str]] = ...) -> None: ...

class ContainerFilesRequest(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str
    def __init__(self, path: _Optional[str] = ...) -> None: ...

class ContainerFilesResponse(_message.Message):
    __slots__ = ("files",)
    FILES_FIELD_NUMBER: _ClassVar[int]
    files: _containers.RepeatedCompositeFieldContainer[FileInfo]
    def __init__(self, files: _Optional[_Iterable[_Union[FileInfo, _Mapping]]] = ...) -> None: ...

class FileInfo(_message.Message):
    __slots__ = ("name", "path", "is_directory", "size", "modified_time")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    IS_DIRECTORY_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_TIME_FIELD_NUMBER: _ClassVar[int]
    name: str
    path: str
    is_directory: bool
    size: int
    modified_time: int
    def __init__(self, name: _Optional[str] = ..., path: _Optional[str] = ..., is_directory: bool = ..., size: _Optional[int] = ..., modified_time: _Optional[int] = ...) -> None: ...

class ContainerRestartResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class AllBackendsStatsResponse(_message.Message):
    __slots__ = ("backend_stats",)
    class BackendStatsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: BackendStats
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[BackendStats, _Mapping]] = ...) -> None: ...
    BACKEND_STATS_FIELD_NUMBER: _ClassVar[int]
    backend_stats: _containers.MessageMap[str, BackendStats]
    def __init__(self, backend_stats: _Optional[_Mapping[str, BackendStats]] = ...) -> None: ...

class PeakEvent(_message.Message):
    __slots__ = ("node_id", "category", "metric", "value", "threshold", "level", "dedupe_key", "context_json", "started_at_ms", "resolved_at_ms", "seq")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    METRIC_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    DEDUPE_KEY_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_JSON_FIELD_NUMBER: _ClassVar[int]
    STARTED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    RESOLVED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    SEQ_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    category: PeakCategory
    metric: str
    value: float
    threshold: float
    level: PeakLevel
    dedupe_key: str
    context_json: str
    started_at_ms: int
    resolved_at_ms: int
    seq: int
    def __init__(self, node_id: _Optional[int] = ..., category: _Optional[_Union[PeakCategory, str]] = ..., metric: _Optional[str] = ..., value: _Optional[float] = ..., threshold: _Optional[float] = ..., level: _Optional[_Union[PeakLevel, str]] = ..., dedupe_key: _Optional[str] = ..., context_json: _Optional[str] = ..., started_at_ms: _Optional[int] = ..., resolved_at_ms: _Optional[int] = ..., seq: _Optional[int] = ...) -> None: ...

class PeakQuery(_message.Message):
    __slots__ = ("since_ms", "until_ms", "category")
    SINCE_MS_FIELD_NUMBER: _ClassVar[int]
    UNTIL_MS_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    since_ms: int
    until_ms: int
    category: PeakCategory
    def __init__(self, since_ms: _Optional[int] = ..., until_ms: _Optional[int] = ..., category: _Optional[_Union[PeakCategory, str]] = ...) -> None: ...
