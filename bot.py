import asyncio
import logging
import sqlite3
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN is not set")
bot = Bot(token=TOKEN)
dp = Dispatcher()
# ================= DB =================
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER UNIQUE,
    name TEXT,
    date TEXT,
    time TEXT,
    price INTEGER DEFAULT 0,
    card TEXT DEFAULT '',
    room TEXT DEFAULT ''
)
''')
conn.commit()
# ================= OWNERS =================
OWNERS = {6279994177, 5857555465}
def is_owner(user_id: int):
    return user_id in OWNERS
# ================= START =================
@dp.message(CommandStart())
async def start(m: Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    await m.answer("■ Bot ■■■■■■■■")
# ================= TOURNAMENT FLOW =================
tour_state = {}
@dp.message(F.text == "/tour")
async def tour(m: Message):
    if not is_owner(m.from_user.id):
        return await m.answer("■■■ ■■■■■■■")
    tour_state[m.from_user.id] = {}
    await m.answer("■■■■■■■ ■■■■■ ■■■■■■■")
@dp.message()
async def flow(m: Message):
    if m.from_user.id not in tour_state:
        return
    data = tour_state[m.from_user.id]
    if "number" not in data:
        data["number"] = int(m.text)
        return await m.answer("■■■■■■■■")
    if "name" not in data:
        data["name"] = m.text
        return await m.answer("■■■■")
    if "date" not in data:
        data["date"] = m.text
        return await m.answer("■■■■■")
    if "time" not in data:
        data["time"] = m.text
        cursor.execute(
            "INSERT INTO tournaments (number,name,date,time) VALUES (?,?,?,?)",
            (data["number"], data["name"], data["date"], data["time"])
        )
        conn.commit()
        del tour_state[m.from_user.id]
        return await m.answer("■■■■■■ ■■■■■■")
# ================= LIST =================
@dp.message(F.text == "/list")
async def list_t(m: Message):
    rows = cursor.execute("SELECT number,name FROM tournaments").fetchall()
    text = "■■■■■■■:"
    for r in rows:
        text += f"■{r[0]} - {r[1]}
"
    await m.answer(text)
# ================= JOIN =================
@dp.message(F.text.startswith("/join"))
async def join(m: Message):
    parts = m.text.split()
    number = int(parts[1])
    tour = cursor.execute(
        "SELECT price,card FROM tournaments WHERE number=?",
        (number,)
    ).fetchone()
    if not tour:
        return await m.answer("■■■ ■■■■■■■")
    price, card = tour
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    await m.answer(f"■■■■: {price}
■■■■■: {card}")
# ================= PRICE =================
@dp.message(F.text.startswith("/price"))
async def price(m: Message):
    if not is_owner(m.from_user.id):
        return
    _, number, value = m.text.split()
    cursor.execute("UPDATE tournaments SET price=? WHERE number=?", (int(value), int(number)))
    conn.commit()
    await m.answer("■■■■ ■■■■■■■■■")
# ================= CARD =================
@dp.message(F.text.startswith("/card"))
async def card(m: Message):
    if not is_owner(m.from_user.id):
        return
    parts = m.text.split(maxsplit=2)
    number = int(parts[1])
    value = parts[2]
    cursor.execute("UPDATE tournaments SET card=? WHERE number=?", (value, number))
    conn.commit()
    await m.answer("■■■■■ ■■■■■■■■■")
# ================= ROOM =================
@dp.message(F.text.startswith("/room"))
async def room(m: Message):
    if not is_owner(m.from_user.id):
        return
    parts = m.text.split(maxsplit=2)
    number = int(parts[1])
    link = parts[2]
    cursor.execute("UPDATE tournaments SET room=? WHERE number=?", (link, number))
    conn.commit()
    await m.answer("■■■■■■■ ■■■■■■■■■")
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
    await m.answer("■■■■■■■■ ■■■■■■■■■■")
# ================= MAIN =================
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
