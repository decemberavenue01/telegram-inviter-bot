import aiosqlite

DB_FILE = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                intro_sent INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        await db.commit()

async def has_seen_intro(user_id: int) -> bool:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT intro_sent FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return False
            return bool(row[0])

async def mark_intro_sent(user_id: int):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE users SET intro_sent = 1 WHERE id = ?", (user_id,))
        await db.commit()

async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
