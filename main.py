import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, USE_REDIS, REDIS_HOST, REDIS_PORT

if USE_REDIS:
    from redis.asyncio import Redis
    from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder

    redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_destiny=True))
else:
    from aiogram.fsm.storage.memory import MemoryStorage

    storage = MemoryStorage()

from handlers import join_handler, broadcast_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

dp.include_router(join_handler.router)
dp.include_router(broadcast_handler.router)

async def main():
    logger.info("Бот запускается...")
    from users_db import init_db
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
