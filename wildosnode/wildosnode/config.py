"""loads config files from environment and env file"""

from enum import Enum
from typing import cast

from decouple import config as _config
from dotenv import load_dotenv

load_dotenv()

SERVICE_ADDRESS: str = cast(str, _config("SERVICE_ADDRESS", default="0.0.0.0", cast=str))
SERVICE_PORT: int = cast(int, _config("SERVICE_PORT", cast=int, default=_config("NODE_GRPC_PORT", cast=int, default=62050)))
INSECURE: bool = cast(bool, _config("INSECURE", cast=bool, default=False))

XRAY_ENABLED: bool = cast(bool, _config("XRAY_ENABLED", cast=bool, default=True))
XRAY_EXECUTABLE_PATH: str = cast(str, _config("XRAY_EXECUTABLE_PATH", default="/usr/bin/xray", cast=str))
XRAY_ASSETS_PATH: str = cast(str, _config("XRAY_ASSETS_PATH", default="/usr/share/xray", cast=str))
XRAY_CONFIG_PATH: str = cast(str, _config("XRAY_CONFIG_PATH", default="/etc/xray/config.json", cast=str))
XRAY_VLESS_REALITY_FLOW: str = cast(str, _config("XRAY_VLESS_REALITY_FLOW", default="xtls-rprx-vision", cast=str))
XRAY_RESTART_ON_FAILURE: bool = cast(bool, _config("XRAY_RESTART_ON_FAILURE", cast=bool, default=False))
XRAY_RESTART_ON_FAILURE_INTERVAL: int = cast(int, _config(
    "XRAY_RESTART_ON_FAILURE_INTERVAL", cast=int, default=0
))

HYSTERIA_ENABLED: bool = cast(bool, _config("HYSTERIA_ENABLED", cast=bool, default=False))
HYSTERIA_EXECUTABLE_PATH: str = cast(str, _config(
    "HYSTERIA_EXECUTABLE_PATH", default="/usr/bin/hysteria", cast=str
))
HYSTERIA_CONFIG_PATH: str = cast(str, _config(
    "HYSTERIA_CONFIG_PATH", default="/etc/hysteria/config.yaml", cast=str
))

SING_BOX_ENABLED: bool = cast(bool, _config("SING_BOX_ENABLED", cast=bool, default=False))
SING_BOX_EXECUTABLE_PATH: str = cast(str, _config(
    "SING_BOX_EXECUTABLE_PATH", default="/usr/bin/sing-box", cast=str
))
SING_BOX_CONFIG_PATH: str = cast(str, _config(
    "SING_BOX_CONFIG_PATH", default="/etc/sing-box/config.json", cast=str
))
SING_BOX_RESTART_ON_FAILURE: bool = cast(bool, _config(
    "SING_BOX_RESTART_ON_FAILURE", cast=bool, default=False
))
SING_BOX_RESTART_ON_FAILURE_INTERVAL: int = cast(int, _config(
    "SING_BOX_RESTART_ON_FAILURE_INTERVAL", cast=int, default=0
))
SING_BOX_USER_MODIFICATION_INTERVAL: int = cast(int, _config(
    "SING_BOX_USER_MODIFICATION_INTERVAL", cast=int, default=30
))


SSL_CERT_FILE: str = cast(str, _config("SSL_CERT_FILE", default="./ssl_cert.pem", cast=str))
SSL_KEY_FILE: str = cast(str, _config("SSL_KEY_FILE", default="./ssl_key.pem", cast=str))
SSL_CLIENT_CERT_FILE: str = cast(str, _config("SSL_CLIENT_CERT_FILE", default="", cast=str))

DEBUG: bool = cast(bool, _config("DEBUG", cast=bool, default=False))


class AuthAlgorithm(Enum):
    PLAIN = "plain"
    XXH128 = "xxh128"


AUTH_GENERATION_ALGORITHM: AuthAlgorithm = cast(AuthAlgorithm, _config(
    "AUTH_GENERATION_ALGORITHM", cast=AuthAlgorithm, default=AuthAlgorithm.XXH128
))
