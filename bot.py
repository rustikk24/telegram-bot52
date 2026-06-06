import asyncio
import logging
import sqlite3
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from aiohttp import web

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN is not set")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= RENDER FIX =================

async def handle(request):
    return web.Response(text="Bot is running")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# ================= DB =================

conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tournaments (
    number INTEGER PRIMARY KEY,
    name TEXT,
    date TEXT,
    time TEXT,
    price INTEGER DEFAULT 0,
    card TEXT DEFAULT '',
    room TEXT DEFAULT ''
)
""")

conn.commit()

# ================= ADMINS =================

OWNERS = {6279994177, 5857555465}

def is_owner(user_id: int):
    return user_id in OWNERS

# ================= START =================

@dp.message(CommandStart())
async def start(m: Message):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (m.from_user.id,))
    conn.commit()
    await m.answer("👋 Бот работает")

# ================= FSM TOUR =================

tour_state = {}

@dp.message(F.text.startswith("/tour"))
async def tour_start(m: Message):
    if not is_owner(m.from_user.id):
        return await m.answer("❌ нет доступа")

    tour_state[m.from_user.id] = {}
    await m.answer("🏆 Введите номер турнира")

@dp.message()
async def tour_flow(m: Message):
    if m.from_user.id not in tour_state:
        return

    data = tour_state[m.from_user.id]

    if "number" not in data:
        try:
            data["number"] = int(m.text)
        except:
            return await m.answer("❌ Введите число")

        return await m.answer("📝 Название турнира")

    if "name" not in data:
        data["name"] = m.text
        return await m.answer("📅 Дата (дд.мм.гггг)")

    if "date" not in data:
        data["date"] = m.text
        return await m.answer("⏰ Время (чч:мм)")

    if "time" not in data:
        data["time"] = m.text

        cursor.execute("""
            INSERT INTO tournaments (number, name, date, time)
            VALUES (?, ?, ?, ?)
        """, (
            data["number"],
            data["name"],
            data["date"],
            data["time"]
        ))

        conn.commit()
        del tour_state[m.from_user.id]

        return await m.answer("✅ Турнир создан")

# ================= LIST =================

@dp.message(F.text == "/list")
async def list_t(m: Message):
    rows = cursor.execute("SELECT number, name FROM tournaments").fetchall()

    if not rows:
        return await m.answer("Нет турниров")

    text = "🏆 Турниры:\n\n"
    for r in rows:
        text += f"№{r[0]} - {r[1]}\n"

    await m.answer(text)

# ================= JOIN =================

@dp.message(F.text.startswith("/join"))
async def join(m: Message):
    parts = m.text.split()

    if len(parts) < 2:
        return await m.answer("Формат: /join 1")

    number = int(parts[1])

    tour = cursor.execute(
        "SELECT price, card FROM tournaments WHERE number=?",
        (number,)
    ).fetchone()

    if not tour:
        return await m.answer("Турнир не найден")

    price, card = tour

    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (m.from_user.id,))
    conn.commit()

    await m.answer(f"💰 Цена: {price}\n💳 Карта: {card}")

# ================= PRICE =================

@dp.message(F.text.startswith("/price"))
async def price(m: Message):
    if not is_owner(m.from_user.id):
        return

    _, number, value = m.text.split()

    cursor.execute(
        "UPDATE tournaments SET price=? WHERE number=?",
        (int(value), int(number))
    )
    conn.commit()

    await m.answer("💰 Цена обновлена")

# ================= CARD =================

@dp.message(F.text.startswith("/card"))
async def card(m: Message):
    if not is_owner(m.from_user.id):
        return

    parts = m.text.split(maxsplit=2)

    if len(parts) < 3:
        return await m.answer("Формат: /card 1 текст")

    number = int(parts[1])
    value = parts[2]

    cursor.execute(
        "UPDATE tournaments SET card=? WHERE number=?",
        (value, number)
    )
    conn.commit()

    await m.answer("💳 Карта обновлена")

# ================= ROOM =================

@dp.message(F.text.startswith("/room"))
async def room(m: Message):
    if not is_owner(m.from_user.id):
        return

    parts = m.text.split(maxsplit=2)

    number = int(parts[1])
    link = parts[2]

    cursor.execute(
        "UPDATE tournaments SET room=? WHERE number=?",
        (link, number)
    )
    conn.commit()

    await m.answer("🎮 Комната обновлена")

# ================= SEND =================

@dp.message(F.text.startswith("/send"))
async def send_all(m: Message):
    if not is_owner(m.from_user.id):
        return

    text = m.text.replace("/send", "").strip()

    users = cursor.execute("SELECT user_id FROM users").fetchall()

    for u in users:
        try:
            await bot.send_message(u[0], text)
        except:
            pass

    await m.answer("📢 Рассылка отправлена")

# ================= MAIN =================

async def main():
    logging.basicConfig(level=logging.INFO)

    await asyncio.gather(
        dp.start_polling(bot),
        web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
