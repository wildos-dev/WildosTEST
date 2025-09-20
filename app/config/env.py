from enum import Enum
from typing import List, cast

from decouple import config
from dotenv import load_dotenv

load_dotenv()

DASHBOARD_PATH: str = cast(str, config("DASHBOARD_PATH", default="/dashboard/", cast=str))

SQLALCHEMY_DATABASE_URL = config(
    "SQLALCHEMY_DATABASE_URL", default="sqlite:///db.sqlite3", cast=str
)
SQLALCHEMY_CONNECTION_POOL_SIZE = config(
    "SQLALCHEMY_CONNECTION_POOL_SIZE", default=10, cast=int
)
SQLALCHEMY_CONNECTION_MAX_OVERFLOW = config(
    "SQLALCHEMY_CONNECTION_MAX_OVERFLOW", default=-1, cast=int
)

UVICORN_HOST: str = cast(str, config("UVICORN_HOST", default="0.0.0.0", cast=str))
UVICORN_PORT = config("UVICORN_PORT", cast=int, default=8000)
UVICORN_UDS: str | None = cast(str | None, config("UVICORN_UDS", default=None, cast=lambda x: x if x else None))
UVICORN_SSL_CERTFILE: str | None = cast(str | None, config("UVICORN_SSL_CERTFILE", default=None, cast=lambda x: x if x else None))
UVICORN_SSL_KEYFILE: str | None = cast(str | None, config("UVICORN_SSL_KEYFILE", default=None, cast=lambda x: x if x else None))


DEBUG = config("DEBUG", default=False, cast=bool)
DOCS = config("DOCS", default=False, cast=bool)


SUBSCRIPTION_URL_PREFIX: str = str(config("SUBSCRIPTION_URL_PREFIX", default="", cast=str)).strip("/")

TELEGRAM_API_TOKEN = config("TELEGRAM_API_TOKEN", default="", cast=str)
TELEGRAM_ADMIN_ID = config(
    "TELEGRAM_ADMIN_ID",
    default="",
    cast=lambda v: [
        int(i) for i in filter(str.isdigit, (s.strip() for s in v.split(",")))
    ],
)
TELEGRAM_PROXY_URL = config("TELEGRAM_PROXY_URL", default="", cast=str)
TELEGRAM_LOGGER_CHANNEL_ID = config(
    "TELEGRAM_LOGGER_CHANNEL_ID", cast=int, default=0
)

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config(
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=1440
)

# Node GRPC configuration
NODE_GRPC_PORT = config("NODE_GRPC_PORT", cast=int, default=62050)

# Admin configuration  
SUDO_USERNAME = config("SUDO_USERNAME", default="admin", cast=str)
SUDO_PASSWORD = config("SUDO_PASSWORD", default="", cast=str)

CUSTOM_TEMPLATES_DIRECTORY = config("CUSTOM_TEMPLATES_DIRECTORY", default=None, cast=lambda x: x if x else None)

SUBSCRIPTION_PAGE_TEMPLATE = config(
    "SUBSCRIPTION_PAGE_TEMPLATE", default="subscription/index.html", cast=str
)
HOME_PAGE_TEMPLATE: str = cast(str, config("HOME_PAGE_TEMPLATE", default="home/index.html", cast=str))

SINGBOX_SUBSCRIPTION_TEMPLATE = config(
    "SINGBOX_SUBSCRIPTION_TEMPLATE", default=None, cast=lambda x: x if x else None
)
XRAY_SUBSCRIPTION_TEMPLATE = config("XRAY_SUBSCRIPTION_TEMPLATE", default=None, cast=lambda x: x if x else None)
CLASH_SUBSCRIPTION_TEMPLATE = config(
    "CLASH_SUBSCRIPTION_TEMPLATE", default=None, cast=lambda x: x if x else None
)

WEBHOOK_ADDRESS = config("WEBHOOK_ADDRESS", default=None, cast=lambda x: x if x else None)
WEBHOOK_SECRET = config("WEBHOOK_SECRET", default=None, cast=lambda x: x if x else None)


class AuthAlgorithm(Enum):
    PLAIN = "plain"
    XXH128 = "xxh128"


AUTH_GENERATION_ALGORITHM = config(
    "AUTH_GENERATION_ALGORITHM",
    cast=AuthAlgorithm,
    default=AuthAlgorithm.XXH128,
)

# recurrent notifications

# timeout between each retry of sending a notification in seconds
RECURRENT_NOTIFICATIONS_TIMEOUT = config(
    "RECURRENT_NOTIFICATIONS_TIMEOUT", default=180, cast=int
)
# how many times to try after ok response not received after sending a notifications
NUMBER_OF_RECURRENT_NOTIFICATIONS = config(
    "NUMBER_OF_RECURRENT_NOTIFICATIONS", default=3, cast=int
)

# sends a notification when the user uses this much of their data
NOTIFY_REACHED_USAGE_PERCENT = config(
    "NOTIFY_REACHED_USAGE_PERCENT", default=80, cast=int
)

# sends a notification when there is n days left of their service
NOTIFY_DAYS_LEFT = config("NOTIFY_DAYS_LEFT", default=3, cast=int)

DISABLE_RECORDING_NODE_USAGE = config(
    "DISABLE_RECORDING_NODE_USAGE", cast=bool, default=False
)

TASKS_RECORD_USER_USAGES_INTERVAL = config(
    "TASKS_RECORD_USER_USAGES_INTERVAL", default=30, cast=int
)
TASKS_REVIEW_USERS_INTERVAL = config(
    "TASKS_REVIEW_USERS_INTERVAL", default=30, cast=int
)
TASKS_EXPIRE_DAYS_REACHED_INTERVAL = config(
    "TASKS_EXPIRE_DAYS_REACHED_INTERVAL", default=30, cast=int
)
TASKS_RESET_USER_DATA_USAGE = config(
    "TASKS_RESET_USER_DATA_USAGE", default=3600, cast=int
)

# CORS security configuration
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
    cast=lambda x: [origin.strip() for origin in x.split(",") if origin.strip()]
)
CORS_ALLOW_CREDENTIALS = config("CORS_ALLOW_CREDENTIALS", default=False, cast=bool)
