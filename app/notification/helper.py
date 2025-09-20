from datetime import datetime
from typing import Dict, Optional

from aiogram import html

from app.models.admin import Admin
from app.models.notification import UserNotification
from app.models.user import UserResponse
from app.utils.system import readable_size


def create_text(notif: UserNotification) -> str:
    data = prepare_data(notif)
    A = UserNotification.Action

    texts: Dict[UserNotification.Action, str] = {
        A.user_created: "🆕 <b>#Created</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username :</b> <code>{username}</code>\n<b>Traffic Limit :</b> <code>{data_limit}</code>\n<b>Expire Date :</b> <code>{expire_date}</code>\n<b>Services :</b> <code>{services}</code>\n➖➖➖➖➖➖➖➖➖\n<b>Belongs To :</b> <code>{owner_username}</code>\n<b>By :</b> <b>#{by}</b>",
        A.user_updated: "✏️ <b>#Modified</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username :</b> <code>{username}</code>\n<b>Traffic Limit :</b> <code>{data_limit}</code>\n<b>Expire Date :</b> <code>{expire_date}</code>\n<b>Services :</b> <code>{services}</code>\n➖➖➖➖➖➖➖➖➖\n<b>Belongs To :</b> <code>{owner_username}</code>\n<b>By :</b> <b>#{by}</b>",
        A.user_activated: "✅ <b>#Activated</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n<b>Belongs To :</b> <code>{owner_username}</code>",
        A.user_deactivated: "❌ <b>#Deactivated</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n<b>Belongs To :</b> <code>{owner_username}</code>",
        A.user_deleted: "🗑 <b>#Deleted</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n➖➖➖➖➖➖➖➖➖\n<b>Belongs To :</b> <code>{owner_username}</code>\n<b>By :</b> <b>#{by}</b>",
        A.user_enabled: "☑️ <b>#Enabled</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n➖➖➖➖➖➖➖➖➖\n<b>Belongs To :</b> <code>{owner_username}</code>\n<b>By :</b> <b>#{by}</b>",
        A.user_disabled: "🛑 <b>#Disabled</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n➖➖➖➖➖➖➖➖➖\n<b>Belongs To :</b> <code>{owner_username}</code>\n<b>By :</b> <b>#{by}</b>",
        A.data_usage_reset: "🔁 <b>#Reset</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n➖➖➖➖➖➖➖➖➖\n<b>By</b> : <b>#{by}</b>",
        A.subscription_revoked: "🔁 <b>#Revoked</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n➖➖➖➖➖➖➖➖➖\n<b>By</b> : <b>#{by}</b>",
        A.reached_usage_percent: "⚠️<b>#DataLimitWarning</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n<b>Used Percent</b> : <code>{usage_percent}</code>\n<b>Remaining Traffic</b> : <code>{remaining_traffic}</code>\n➖➖➖➖➖➖➖➖➖\n<b>Belongs To :</b> <code>{owner_username}</code>",
        A.reached_days_left: "⚠️<b>#ExpirationWarning</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n<b>Remaining Days</b> : <code>{remaining_days}</code>\n➖➖➖➖➖➖➖➖➖\n<b>Belongs To :</b> <code>{owner_username}</code>",
    }

    notif_action = getattr(notif, 'action', None)
    if notif_action == A.user_deactivated and not getattr(notif, 'by', None):
        if notif.user.expired:
            texts[A.user_deactivated] = (
                "🕔 <b>#Expired</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n<b>Belongs To :</b> <code>{owner_username}</code>"
            )
        elif notif.user.data_limit_reached:
            texts[A.user_deactivated] = (
                "🪫 <b>#Limited</b>\n➖➖➖➖➖➖➖➖➖\n<b>Username</b> : <code>{username}</code>\n<b>Belongs To :</b> <code>{owner_username}</code>"
            )

    action = getattr(notif, 'action', None)
    text = texts.get(action) if action else None
    if text:
        formatted_message = text.format_map(data)
    else:
        formatted_message = f"Unknown notification: {getattr(notif, 'action', 'no action')}"

    return formatted_message


def prepare_data(notif: UserNotification) -> dict:
    user = UserResponse.model_validate(notif.user)
    by_attr = getattr(notif, "by", None)
    by: Optional[Admin] = (
        Admin.model_validate(by_attr)
        if by_attr
        else None
    )
    data = {
        "username": html.quote(user.username),
        "data_limit": (
            readable_size(user.data_limit) if user.data_limit else "Unlimited"
        ),
        "remaining_traffic": (
            readable_size(max(user.data_limit - user.used_traffic, 0))
            if user.data_limit
            else "Unlimited"
        ),
        "usage_percent": (
            f"{round(min((user.used_traffic / user.data_limit) * 100, 100),2)}%"
            if isinstance(user.data_limit, int) and user.data_limit > 0
            else "0%"
        ),
        "expire_date": (
            user.expire_date.strftime("%H:%M:%S %Y-%m-%d")
            if user.expire_date
            else "Never"
        ),
        "remaining_days": (
            (user.expire_date - datetime.now()).days
            if user.expire_date
            else "Never"
        ),
        "services": user.service_ids if user.service_ids else "",
        "owner_username": user.owner_username,
        "by": html.quote(by.username) if by else None,
    }

    return data
