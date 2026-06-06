cursor.execute(
        "UPDATE tournaments SET price=? WHERE number=?",
        (int(price), int(number))
    )
    conn.commit()

    await m.answer("💰 Цена обновлена")

# ================= CARD =================

@dp.message(F.text.startswith("/card"))
async def set_card(m: Message):
    if not is_owner(m.from_user.id):
        return

    parts = m.text.split(maxsplit=2)

    number = int(parts[1])
    card = parts[2]

    cursor.execute(
        "UPDATE tournaments SET card=? WHERE number=?",
        (card, number)
    )
    conn.commit()

    await m.answer("💳 Реквизиты обновлены")

# ================= ROOM =================

@dp.message(F.text.startswith("/room"))
async def set_room(m: Message):
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

    await m.answer("🎮 Комната добавлена")

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
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())