import asyncio
import logging
import sqlite3
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8991980936:AAGMYCNcD0fxALcsrnhXAFt8IH87AHtSiX4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ----- БД -----
conn = sqlite3.connect("scam.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    ref_id INTEGER DEFAULT 0,
    balance REAL DEFAULT 0,
    total_earned REAL DEFAULT 0,
    join_date TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    date TEXT
)
""")
conn.commit()

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def reg_user(user_id, username, ref_id=0):
    if get_user(user_id): return
    cur.execute("INSERT INTO users (user_id, username, ref_id, join_date) VALUES (?,?,?,?)",
                (user_id, username, ref_id, datetime.date.today().isoformat()))
    conn.commit()

def top_all():
    return cur.execute("SELECT user_id, username, total_earned FROM users ORDER BY total_earned DESC LIMIT 10").fetchall()

def top_day():
    return cur.execute("""
        SELECT user_id, username, SUM(amount) as s FROM deposits
        WHERE date=?
        GROUP BY user_id ORDER BY s DESC LIMIT 10
    """, (datetime.date.today().isoformat(),)).fetchall()

def top_week():
    w = datetime.date.today() - datetime.timedelta(days=7)
    return cur.execute("""
        SELECT user_id, username, SUM(amount) as s FROM deposits
        WHERE date>=?
        GROUP BY user_id ORDER BY s DESC LIMIT 10
    """, (w.isoformat(),)).fetchall()

# ----- КНОПКИ -----
def main_kb():
    b = InlineKeyboardBuilder()
    b.button(text="📊 О проекте", callback_data="about")
    b.button(text="👤 Кураторы", callback_data="curators")
    b.button(text="🏆 Топ дня", callback_data="top_day")
    b.button(text="🏆 Топ недели", callback_data="top_week")
    b.button(text="🏆 Топ за всё время", callback_data="top_all")
    b.button(text="💰 Пополнить", callback_data="deposit")
    b.button(text="👥 Рефералы", callback_data="refs")
    b.adjust(2)
    return b.as_markup()

# ----- СТАРТ -----
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    reg_user(message.from_user.id, message.from_user.username or f"id{message.from_user.id}", ref_id)
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Добро пожаловать в **ZK Pride** — лучший скам-проект 2025 🔥\n"
        f"Зарабатывай лёгкие деньги, приглашай друзей и забирай профит!\n\n"
        f"👇 Выбери раздел:",
        reply_markup=main_kb()
    )

# ----- О ПРОЕКТЕ -----
@dp.callback_query(lambda c: c.data == "about")
async def about(call: types.CallbackQuery):
    await call.message.edit_text(
        "📊 **О проекте ZK Pride**\n\n"
        "🔹 Зарабатывай на рефералах — до 30% от вкладов\n"
        "🔹 Минималка от 100 руб\n"
        "🔹 Выплаты каждый день\n"
        "🔹 Работаем с 2024 года\n\n"
        "**Схема:**\n"
        "1. Пополняешь баланс\n"
        "2. Приглашаешь друзей по ссылке\n"
        "3. Получаешь % с их пополнений\n"
        "4. Выводишь заработанное\n\n"
        "🔥 Уже выплачено: **1 240 000+ руб**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

# ----- КУРАТОРЫ -----
@dp.callback_query(lambda c: c.data == "curators")
async def curators(call: types.CallbackQuery):
    await call.message.edit_text(
        "👤 **Кураторы проекта**\n\n"
        "1️⃣ @CryptoKing — топ-куратор (выплаты: 340 000 руб)\n"
        "2️⃣ @FastMoney — куратор (выплаты: 210 000 руб)\n"
        "3️⃣ @RichBro — куратор (выплаты: 150 000 руб)\n"
        "4️⃣ @LuckyStar — куратор (выплаты: 95 000 руб)\n\n"
        "Хочешь стать куратором? Пиши @ZkSupport",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

# ----- ТОПЫ -----
@dp.callback_query(lambda c: c.data == "top_day")
async def top_day_handler(call: types.CallbackQuery):
    t = top_day()
    if not t:
        text = "🏆 **Топ дня**\n\nПока пусто. Будь первым!"
    else:
        text = "🏆 **Топ дня**\n\n"
        for i, (uid, uname, s) in enumerate(t, 1):
            text += f"{i}. @{uname} — {s:.0f} руб\n"
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]))

@dp.callback_query(lambda c: c.data == "top_week")
async def top_week_handler(call: types.CallbackQuery):
    t = top_week()
    if not t:
        text = "🏆 **Топ недели**\n\nПока пусто."
    else:
        text = "🏆 **Топ недели**\n\n"
        for i, (uid, uname, s) in enumerate(t, 1):
            text += f"{i}. @{uname} — {s:.0f} руб\n"
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]))

@dp.callback_query(lambda c: c.data == "top_all")
async def top_all_handler(call: types.CallbackQuery):
    t = top_all()
    if not t:
        text = "🏆 **Топ за всё время**\n\nПока пусто."
    else:
        text = "🏆 **Топ за всё время**\n\n"
        for i, (uid, uname, s) in enumerate(t, 1):
            text += f"{i}. @{uname} — {s:.0f} руб\n"
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]))

# ----- ПОПОЛНЕНИЕ -----
@dp.callback_query(lambda c: c.data == "deposit")
async def deposit(call: types.CallbackQuery):
    await call.message.edit_text(
        "💰 **Пополнение баланса**\n\n"
        "Переведи любую сумму на кошелёк ниже и отправь скриншот @ZkSupport\n\n"
        "**QIWI:** +7-999-123-45-67\n"
        "**СБП:** 8-800-555-35-35\n"
        "**USDT (TRC20):** TXYZ...ваш_адрес\n\n"
        "⚠️ Минималка: 100 руб\n"
        "⚠️ Комиссия: 0%",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

# ----- РЕФЕРАЛЫ -----
@dp.callback_query(lambda c: c.data == "refs")
async def refs(call: types.CallbackQuery):
    uid = call.from_user.id
    u = get_user(uid)
    if not u:
        await call.answer("Сначала запусти бота")
        return
    cur.execute("SELECT COUNT(*) FROM users WHERE ref_id=?", (uid,))
    ref_count = cur.fetchone()[0]
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"
    await call.message.edit_text(
        f"👥 **Рефералы**\n\n"
        f"Приглашено: **{ref_count} чел**\n"
        f"Заработано: **{u[4]:.0f} руб**\n\n"
        f"Твоя реферальная ссылка:\n`{ref_link}`\n\n"
        f"🔥 Ты получаешь 30% от каждого пополнения реферала!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

# ----- НАЗАД -----
@dp.callback_query(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.edit_text(
        "👇 Выбери раздел:",
        reply_markup=main_kb()
    )

# ----- ЗАПУСК -----
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

