import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from app.config import TELEGRAM_PROXY_URL
from app.config.env import (
    TELEGRAM_API_TOKEN,
    TELEGRAM_ADMIN_ID,
    TELEGRAM_LOGGER_CHANNEL_ID,
)
from app.models.notification import UserNotification
from app.notification.helper import create_text

logger = logging.getLogger(__name__)


class BotManager:
    _instance = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None and TELEGRAM_API_TOKEN and str(TELEGRAM_API_TOKEN).strip():
            session = None
            if TELEGRAM_PROXY_URL and str(TELEGRAM_PROXY_URL).strip():
                session = AiohttpSession(proxy=str(TELEGRAM_PROXY_URL))

            cls._instance = Bot(
                token=str(TELEGRAM_API_TOKEN),
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
                session=session,
            )
            try:
                await cls._instance.get_me()
            except:
                logger.error("Telegram API token is not valid.")
        return cls._instance


async def send_message(
    message: str,
    parse_mode=ParseMode.HTML,
):
    if not (bot := await BotManager.get_instance()):
        return

    admin_ids = list(TELEGRAM_ADMIN_ID) if TELEGRAM_ADMIN_ID and isinstance(TELEGRAM_ADMIN_ID, list) else []
    logger_id = [TELEGRAM_LOGGER_CHANNEL_ID] if TELEGRAM_LOGGER_CHANNEL_ID else []
    
    for recipient_id in admin_ids + logger_id:
        if not recipient_id:
            continue
        try:
            await bot.send_message(
                recipient_id,
                message,
                parse_mode=parse_mode,
            )
        except TelegramAPIError as e:
            logger.error(e)


async def send_notification(notif: UserNotification):
    text = create_text(notif)
    await send_message(text)
