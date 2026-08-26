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
conn = sqlite3.connect("narko.db", check_same_thread=False)
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
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product TEXT,
    amount REAL,
    status TEXT DEFAULT 'ожидание',
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
        SELECT user_id, username, SUM(amount) as s FROM orders
        WHERE date=? AND status='выполнен'
        GROUP BY user_id ORDER BY s DESC LIMIT 10
    """, (datetime.date.today().isoformat(),)).fetchall()

def top_week():
    w = datetime.date.today() - datetime.timedelta(days=7)
    return cur.execute("""
        SELECT user_id, username, SUM(amount) as s FROM orders
        WHERE date>=? AND status='выполнен'
        GROUP BY user_id ORDER BY s DESC LIMIT 10
    """, (w.isoformat(),)).fetchall()

# ----- КНОПКИ -----
def main_kb():
    b = InlineKeyboardBuilder()
    b.button(text="📋 Товары", callback_data="products")
    b.button(text="👤 Профиль", callback_data="profile")
    b.button(text="👥 Рефералы", callback_data="refs")
    b.button(text="🏆 Топ дня", callback_data="top_day")
    b.button(text="🏆 Топ недели", callback_data="top_week")
    b.button(text="🏆 Топ за всё", callback_data="top_all")
    b.button(text="📞 Саппорт", callback_data="support")
    b.adjust(2)
    return b.as_markup()

# ----- ПРАЙС -----
products_list = {
    "🔊 Мефедрон": {"price": 2500, "unit": "гр", "info": "Кристаллы, чистота 95%+"},
    "❄️ Кокаин": {"price": 7000, "unit": "гр", "info": "Колумбийский, перуанский"},
    "💊 MDMA": {"price": 1500, "unit": "шт", "info": "Кристаллы, экстази"},
    "🌿 Гашиш": {"price": 1200, "unit": "гр", "info": "Марокканский, сухой"},
    "🧊 Альфа": {"price": 3000, "unit": "гр", "info": "Альфа-PVP, соль"},
    "🍄 Грибы": {"price": 3500, "unit": "гр", "info": "Псилоцибиновые"},
    "💊 Ксанакс": {"price": 800, "unit": "бл", "info": "Фарма, 1 мг"},
    "💊 Лирика": {"price": 1500, "unit": "бл", "info": "Прегабалин 300 мг"},
    "🧪 Амфетамин": {"price": 2000, "unit": "гр", "info": "Порошок, скорость"},
}

# ----- СТАРТ -----
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    reg_user(message.from_user.id, message.from_user.username or f"id{message.from_user.id}", ref_id)
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Добро пожаловать в **Vault Shop** 🔥\n"
        f"Лучший маркетплейс с 2023 года\n"
        f"Работаем 24/7 | Доставка по всей РФ\n\n"
        f"👇 Выбери раздел:",
        reply_markup=main_kb()
    )

# ----- ТОВАРЫ -----
@dp.callback_query(lambda c: c.data == "products")
async def products(call: types.CallbackQuery):
    text = "📋 **Наш ассортимент:**\n\n"
    for name, info in products_list.items():
        text += f"{name} — **{info['price']} руб/{info['unit']}**\n"
    text += "\nДля заказа нажми на товар ниже 👇"

    b = InlineKeyboardBuilder()
    for name in products_list:
        b.button(text=name, callback_data=f"prod_{name}")
    b.button(text="◀️ Назад", callback_data="back")
    b.adjust(2)

    await call.message.edit_text(text, reply_markup=b.as_markup())

@dp.callback_query(lambda c: c.data.startswith("prod_"))
async def product_detail(call: types.CallbackQuery):
    name = call.data.replace("prod_", "")
    info = products_list[name]
    await call.message.edit_text(
        f"{name}\n\n"
        f"💰 Цена: **{info['price']} руб/{info['unit']}**\n"
        f"ℹ️ {info['info']}\n\n"
        f"Для оформления заказа напиши @nezovime",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Заказать", url="https://t.me/nezovime")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="products")]
        ])
    )

# ----- ПРОФИЛЬ -----
@dp.callback_query(lambda c: c.data == "profile")
async def profile(call: types.CallbackQuery):
    u = get_user(call.from_user.id)
    if not u:
        await call.answer("Сначала запусти бота через /start")
        return
    cur.execute("SELECT COUNT(*) FROM users WHERE ref_id=?", (call.from_user.id,))
    refs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (call.from_user.id,))
    orders_count = cur.fetchone()[0]
    await call.message.edit_text(
        f"👤 **Профиль**\n\n"
        f"🔹 ID: `{call.from_user.id}`\n"
        f"🔹 Юзер: @{call.from_user.username or 'нет'}\n"
        f"🔹 Рефералов: {refs}\n"
        f"🔹 Заказов: {orders_count}\n"
        f"🔹 Заработано: {u[4]:.0f} руб\n"
        f"🔹 На балансе: {u[3]:.0f} руб\n"
        f"🔹 Дата регистрации: {u[5]}\n\n"
        f"По всем вопросам — @nezovime",
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
        f"🔥 Ты получаешь 20% от каждого заказа реферала!\n\n"
        f"Забрать выплату — @nezovime",
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

# ----- САППОРТ -----
@dp.callback_query(lambda c: c.data == "support")
async def support(call: types.CallbackQuery):
    await call.message.edit_text(
        "📞 **Поддержка**\n\n"
        "По всем вопросам — @nezovime\n\n"
        "🔹 Заказы\n"
        "🔹 Выплаты\n"
        "🔹 Реклама\n"
        "🔹 Сотрудничество\n\n"
        "Отвечаем в течение 5-15 минут",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать", url="https://t.me/nezovime")],
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

