import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_USERNAME = os.getenv("OWNER_USERNAME", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))

ADMIN_IDS = [
    int(uid) for uid in os.getenv("ADMIN_IDS", "").split(",")
    if uid.strip().isdigit()
]

CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

USE_REDIS = False