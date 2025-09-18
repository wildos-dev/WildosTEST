from fastapi import APIRouter

from app.config.env import NODE_GRPC_PORT
from app.db import crud
from app.db.models import Admin as DBAdmin, Settings
from app.db.models import Node
from app.dependencies import (
    DBDep,
    AdminDep,
    SudoAdminDep,
    EndDateDep,
    StartDateDep,
)
from app.models.node import NodeStatus
from app.models.settings import SubscriptionSettings, TelegramSettings
from app.models.system import (
    UsersStats,
    NodesStats,
    AdminsStats,
    TrafficUsageSeries,
)
from app.models.user import UserExpireStrategy

router = APIRouter(tags=["System"], prefix="/system")


@router.get("/settings/subscription", response_model=SubscriptionSettings)
def get_subscription_settings(db: DBDep, admin: SudoAdminDep):
    settings = db.query(Settings).first()
    if not settings:
        # Create default settings if none exist (from marzneshin)
        default_subscription = {
            "template_on_acceptance": True,
            "profile_title": "Support",
            "support_link": "t.me/support",
            "update_interval": 12,
            "shuffle_configs": False,
            "placeholder_if_disabled": True,
            "placeholder_remark": "disabled",
            "rules": [
                {"pattern": "^([Cc]lash-verge|[Cc]lash-?[Mm]eta)", "result": "clash-meta"},
                {"pattern": "^([Cc]lash|[Ss]tash)", "result": "clash"},
                {"pattern": "^(SFA|SFI|SFM|SFT|[Kk]aring|[Hh]iddify[Nn]ext)", "result": "sing-box"},
                {"pattern": "^v2rayN/(?:6\\.(?:[5-9]\\d+|4[1-9])|[7-9]\\d*\\.\\d+)", "result": "xray"},
                {"pattern": "^v2rayN/", "result": "base64-links"},
                {"pattern": "^v2rayNG/([2-9]|1\\.(9|\\d{2,})|1\\.8\\.(1[7-9]|[2-9]\\d|\\d{3,}))", "result": "xray"},
                {"pattern": "^v2rayNG/", "result": "base64-links"},
                {"pattern": "^[Ss]treisand", "result": "xray"},
                {"pattern": ".*", "result": "base64-links"}
            ]
        }
        settings = Settings(subscription=default_subscription, telegram=None)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings.subscription


@router.put("/settings/subscription", response_model=SubscriptionSettings)
def update_subscription_settings(
    db: DBDep, modifications: SubscriptionSettings, admin: SudoAdminDep
):
    settings = db.query(Settings).first()
    if not settings:
        # Create default settings if none exist
        settings = Settings(subscription=modifications.model_dump(mode="json"), telegram=None)
        db.add(settings)
    else:
        # Update existing settings
        db.query(Settings).filter(Settings.id == settings.id).update({
            "subscription": modifications.model_dump(mode="json")
        })
        db.refresh(settings)
    db.commit()
    db.refresh(settings)
    return settings.subscription


@router.get("/settings/telegram", response_model=TelegramSettings | None)
def get_telegram_settings(db: DBDep, admin: SudoAdminDep):
    settings = db.query(Settings).first()
    if not settings:
        # Create default settings if none exist (from marzneshin)
        default_subscription = {
            "template_on_acceptance": True,
            "profile_title": "Support",
            "support_link": "t.me/support",
            "update_interval": 12,
            "shuffle_configs": False,
            "placeholder_if_disabled": True,
            "placeholder_remark": "disabled",
            "rules": [
                {"pattern": "^([Cc]lash-verge|[Cc]lash-?[Mm]eta)", "result": "clash-meta"},
                {"pattern": "^([Cc]lash|[Ss]tash)", "result": "clash"},
                {"pattern": "^(SFA|SFI|SFM|SFT|[Kk]aring|[Hh]iddify[Nn]ext)", "result": "sing-box"},
                {"pattern": "^v2rayN/(?:6\\.(?:[5-9]\\d+|4[1-9])|[7-9]\\d*\\.\\d+)", "result": "xray"},
                {"pattern": "^v2rayN/", "result": "base64-links"},
                {"pattern": "^v2rayNG/([2-9]|1\\.(9|\\d{2,})|1\\.8\\.(1[7-9]|[2-9]\\d|\\d{3,}))", "result": "xray"},
                {"pattern": "^v2rayNG/", "result": "base64-links"},
                {"pattern": "^[Ss]treisand", "result": "xray"},
                {"pattern": ".*", "result": "base64-links"}
            ]
        }
        settings = Settings(subscription=default_subscription, telegram=None)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings.telegram


@router.put("/settings/telegram", response_model=TelegramSettings | None)
def update_telegram_settings(
    db: DBDep, new_telegram: TelegramSettings | None, admin: SudoAdminDep
):
    settings = db.query(Settings).first()
    if not settings:
        # Create default settings if none exist (from marzneshin)
        default_subscription = {
            "template_on_acceptance": True,
            "profile_title": "Support",
            "support_link": "t.me/support",
            "update_interval": 12,
            "shuffle_configs": False,
            "placeholder_if_disabled": True,
            "placeholder_remark": "disabled",
            "rules": [
                {"pattern": "^([Cc]lash-verge|[Cc]lash-?[Mm]eta)", "result": "clash-meta"},
                {"pattern": "^([Cc]lash|[Ss]tash)", "result": "clash"},
                {"pattern": "^(SFA|SFI|SFM|SFT|[Kk]aring|[Hh]iddify[Nn]ext)", "result": "sing-box"},
                {"pattern": "^v2rayN/(?:6\\.(?:[5-9]\\d+|4[1-9])|[7-9]\\d*\\.\\d+)", "result": "xray"},
                {"pattern": "^v2rayN/", "result": "base64-links"},
                {"pattern": "^v2rayNG/([2-9]|1\\.(9|\\d{2,})|1\\.8\\.(1[7-9]|[2-9]\\d|\\d{3,}))", "result": "xray"},
                {"pattern": "^v2rayNG/", "result": "base64-links"},
                {"pattern": "^[Ss]treisand", "result": "xray"},
                {"pattern": ".*", "result": "base64-links"}
            ]
        }
        telegram_data = new_telegram.model_dump(mode="json") if new_telegram else None
        settings = Settings(subscription=default_subscription, telegram=telegram_data)
        db.add(settings)
    else:
        # Update existing settings
        telegram_data = new_telegram.model_dump(mode="json") if new_telegram else None
        db.query(Settings).filter(Settings.id == settings.id).update({
            "telegram": telegram_data
        })
        db.refresh(settings)
    db.commit()
    db.refresh(settings)
    return settings.telegram


@router.get("/config/node-grpc-port")
def get_node_grpc_port(admin: AdminDep):
    """Get the default NODE_GRPC_PORT for node configuration"""
    return {"port": NODE_GRPC_PORT}


@router.get("/stats/admins", response_model=AdminsStats)
def get_admins_stats(db: DBDep, admin: SudoAdminDep):
    return AdminsStats(total=db.query(DBAdmin).count())


@router.get("/stats/nodes", response_model=NodesStats)
def get_nodes_stats(db: DBDep, admin: SudoAdminDep):
    return NodesStats(
        total=db.query(Node).count(),
        healthy=db.query(Node)
        .filter(Node.status == NodeStatus.healthy)
        .count(),
        unhealthy=db.query(Node)
        .filter(Node.status == NodeStatus.unhealthy)
        .count(),
    )


@router.get("/stats/traffic", response_model=TrafficUsageSeries)
def get_total_traffic_stats(
    db: DBDep, admin: AdminDep, start_date: StartDateDep, end_date: EndDateDep
):
    return crud.get_total_usages(db, admin, start_date, end_date)  # type: ignore


@router.get("/stats/users", response_model=UsersStats)
def get_users_stats(db: DBDep, admin: AdminDep):
    return UsersStats(
        total=crud.get_users_count(
            db, admin=admin if not admin.is_sudo else None  # type: ignore
        ),
        active=crud.get_users_count(
            db, admin=admin if not admin.is_sudo else None, is_active=True  # type: ignore
        ),
        on_hold=crud.get_users_count(
            db,
            admin=admin if not admin.is_sudo else None,  # type: ignore
            expire_strategy=UserExpireStrategy.START_ON_FIRST_USE,
        ),
        expired=crud.get_users_count(
            db,
            admin=admin if not admin.is_sudo else None,  # type: ignore
            expired=True,
        ),
        limited=crud.get_users_count(
            db,
            admin=admin if not admin.is_sudo else None,  # type: ignore
            data_limit_reached=True,
        ),
        online=crud.get_users_count(
            db, admin=admin if not admin.is_sudo else None, online=True  # type: ignore
        ),
    )
