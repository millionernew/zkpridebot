import asyncio
import logging
import sqlite3
import datetime
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8991980936:AAGMYCNcD0fxALcsrnhXAFt8IH87AHtSiX4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ----- БД -----
conn = sqlite3.connect("shadow.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    ref_id INTEGER DEFAULT 0,
    balance REAL DEFAULT 0,
    total_earned REAL DEFAULT 0,
    level INTEGER DEFAULT 1,
    exp INTEGER DEFAULT 0,
    join_date TEXT,
    last_bonus TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product TEXT,
    quantity INTEGER,
    city TEXT,
    amount REAL,
    status TEXT DEFAULT '![⏳](tg://emoji?id=6016961981527897114) Ожидание',
    date TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    text TEXT,
    rating INTEGER,
    date TEXT
)
""")
conn.commit()

# ----- УРОВНИ -----
levels = {
    1: "🌑 Новичок",
    2: "🌘 Заинтересованный",
    3: "🌗 Свой",
    4: "🌖 Постоянный",
    5: "🌕 Легенда",
    6: "![💎](tg://emoji?id=6016882537517818399) Элита",
    7: "👑 Бог рынка"
}

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def reg_user(user_id, username, ref_id=0):
    if get_user(user_id): return
    cur.execute("INSERT INTO users (user_id, username, ref_id, join_date) VALUES (?,?,?,?)",
                (user_id, username, ref_id, datetime.date.today().isoformat()))
    conn.commit()

def add_exp(user_id, amount):
    u = get_user(user_id)
    if not u: return
    new_exp = u[5] + amount
    new_level = u[4]
    exp_needed = new_level * 100
    if new_exp >= exp_needed and new_level < 7:
        new_level += 1
        new_exp = 0
    cur.execute("UPDATE users SET exp=?, level=? WHERE user_id=?", (new_exp, new_level, user_id))
    conn.commit()
    return new_level > u[4]

# ----- ТОВАРЫ -----
products_list = {
    "🔊 Мефедрон": {"price": 2500, "unit": "гр", "emoji": "🔊"},
    "❄️ Кокаин": {"price": 7000, "unit": "гр", "emoji": "❄️"},
    "💊 MDMA": {"price": 1500, "unit": "шт", "emoji": "💊"},
    "🌿 Гашиш": {"price": 1200, "unit": "гр", "emoji": "🌿"},
    "🧊 Альфа-PVP": {"price": 3000, "unit": "гр", "emoji": "🧊"},
    "🍄 Грибы": {"price": 3500, "unit": "гр", "emoji": "🍄"},
    "💊 Ксанакс": {"price": 800, "unit": "бл", "emoji": "💊"},
    "🧪 Амфетамин": {"price": 2000, "unit": "гр", "emoji": "🧪"},
}

# ----- КНОПКИ -----
def main_kb():
    b = InlineKeyboardBuilder()
    b.button(text="📋 Товары", callback_data="products")
    b.button(text="![👤](tg://emoji?id=6016827493216951665) Профиль", callback_data="profile")
    b.button(text="![🎁](tg://emoji?id=6017352625983331333) Бонус дня", callback_data="bonus")
    b.button(text="🎲 Орёл/Решка", callback_data="coinflip")
    b.button(text="![👥](tg://emoji?id=6017207340124611376) Рефералы", callback_data="refs")
    b.button(text="![📞](tg://emoji?id=6016903402468940975) Саппорт", callback_data="support")
    b.adjust(2)
    return b.as_markup()

# ----- СТАРТ -----
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    reg_user(message.from_user.id, message.from_user.username or f"id{message.from_user.id}", ref_id)

    await message.answer(
        f"![🌙](tg://emoji?id=6017227977442466906) **Добро пожаловать в Shadow Market**\n\n"
        f"Привет, **{message.from_user.first_name}**\n"
        f"Ты попал в самое надёжное место во всём даркнете 🔥\n\n"
        f"▸ Работаем с 2022\n"
        f"▸ 3000+ довольных клиентов\n"
        f"▸ Доставка 24/7 по всей РФ\n"
        f"▸ Анонимно | Быстро | Качественно\n\n"
        f"_«Тени не исчезают — они ждут»_ 🖤",
        reply_markup=main_kb()
    )

# ----- ТОВАРЫ -----
@dp.callback_query(lambda c: c.data == "products")
async def products(call: types.CallbackQuery):
    text = "📋 **Каталог Shadow Market**\n\n"
    for name, info in products_list.items():
        text += f"{info['emoji']} **{name}** — `{info['price']} руб/{info['unit']}`\n"
    text += "\n👇 Выбери товар:"

    b = InlineKeyboardBuilder()
    for name in products_list:
        emj = products_list[name]["emoji"]
        b.button(text=f"{emj} {name}", callback_data=f"prod_{name}")
    b.button(text="◀️ Назад", callback_data="back")
    b.adjust(2)

    await call.message.edit_text(text, reply_markup=b.as_markup())

@dp.callback_query(lambda c: c.data.startswith("prod_"))
async def product_detail(call: types.CallbackQuery):
    name = call.data.replace("prod_", "")
    info = products_list[name]
    b = InlineKeyboardBuilder()
    b.button(text="🛒 Заказать", callback_data=f"order_{name}")
    b.button(text="◀️ Назад", callback_data="products")
    await call.message.edit_text(
        f"{info['emoji']} **{name}**\n\n"
        f"![💳](tg://emoji?id=6016901577107839515) Цена: **{info['price']} руб/{info['unit']}**\n"
        f"📦 Фасовка: от 0.5 {info['unit']}\n"
        f"![✅](tg://emoji?id=6016835129668803369) Гарантия: 100%\n"
        f"🚚 Доставка: от 30 мин\n\n"
        f"_Нажми «Заказать» и наш оператор свяжется с тобой_",
        reply_markup=b.as_markup()
    )

@dp.callback_query(lambda c: c.data.startswith("order_"))
async def order_product(call: types.CallbackQuery):
    name = call.data.replace("order_", "")
    info = products_list[name]
    await call.message.edit_text(
        f"![✅](tg://emoji?id=6016835129668803369) **Запрос на {name} отправлен!**\n\n"
        f"![📌](tg://emoji?id=6017218803392323084) **Реквизиты для оплаты:**\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🔹 **СБП:** `+79048578036`\n"
        f"🔹 **Сбербанк:** Константин К\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"![💳](tg://emoji?id=6016901577107839515) Сумма: **{info['price']} руб/{info['unit']}**\n\n"
        f"После оплаты отправь **скриншот** @nezovime\n"
        f"Оператор подтвердит платеж и договорится о доставке ![✅](tg://emoji?id=6016835129668803369)\n\n"
        f"![⏳](tg://emoji?id=6016961981527897114) Среднее время подтверждения: 5-10 мин",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="![💬](tg://emoji?id=6015050016706535016) Написать оператору", url="https://t.me/nezovime")],
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

    level_name = levels.get(u[4], "🌑 Новичок")
    exp_needed = u[4] * 100
    exp_bar = "▓" * (u[5] // 10) + "░" * (10 - u[5] // 10) if u[5] < exp_needed else "▓" * 10

    cur.execute("SELECT COUNT(*) FROM users WHERE ref_id=?", (call.from_user.id,))
    refs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (call.from_user.id,))
    orders_count = cur.fetchone()[0]

    await call.message.edit_text(
        f"🖤 **Shadow Profile**\n\n"
        f"▸ Юзер: @{call.from_user.username or 'нет'}\n"
        f"▸ ID: `{call.from_user.id}`\n"
        f"▸ Ранг: {level_name}\n"
        f"▸ Опыт: `{u[5]}/{exp_needed}`\n"
        f"▸ Прогресс: `{exp_bar}`\n"
        f"▸ Рефералов: **{refs}**\n"
        f"▸ Заказов: **{orders_count}**\n"
        f"▸ Заработано: **{u[4]:.0f} руб**\n"
        f"▸ Дата: {u[6]}\n\n"
        f"_«Каждый заказ приближает тебя к легенде»_ 🖤",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

# ----- БОНУС ДНЯ -----
@dp.callback_query(lambda c: c.data == "bonus")
async def daily_bonus(call: types.CallbackQuery):
    u = get_user(call.from_user.id)
    if not u:
        await call.answer("Сначала запусти бота")
        return

    today = datetime.date.today().isoformat()
    if u[7] == today:
        await call.message.edit_text(
            "![🎁](tg://emoji?id=6017352625983331333) **Бонус дня**\n\n"
            "Ты уже получил свой бонус сегодня!\n"
            "Возвращайся завтра ![🌙](tg://emoji?id=6017227977442466906)\n\n"
            "_Новый бонус доступен каждые 24 часа_",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
        )
        return

    bonus = random.randint(100, 500)
    cur.execute("UPDATE users SET balance=balance+?, last_bonus=? WHERE user_id=?",
                (bonus, today, call.from_user.id))
    conn.commit()
    add_exp(call.from_user.id, 20)

    await call.message.edit_text(
        f"![🎁](tg://emoji?id=6017352625983331333) **Ежедневный бонус получен!**\n\n"
        f"▸ Начислено: **+{bonus} руб** 🤑\n"
        f"▸ Опыт: **+20 EXP** ⭐\n\n"
        f"Заходи завтра за новым бонусом!\n"
        f"_Каждый день — халявные деньги_ 🔥",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

# ----- ОРЁЛ/РЕШКА -----
@dp.callback_query(lambda c: c.data == "coinflip")
async def coinflip_menu(call: types.CallbackQuery):
    bal = get_user(call.from_user.id)[3] if get_user(call.from_user.id) else 0
    await call.message.edit_text(
        f"🎲 **Орёл & Решка**\n\n"
        f"Правила простые:\n"
        f"▸ Выбери ставку\n"
        f"▸ Угадай Орёл или Решка\n"
        f"▸ Угадал — **x2** твоя ставка\n"
        f"▸ Не угадал — ставка сгорает\n\n"
        f"💰 Твой баланс: **{bal} руб**\n\n"
        f"👇 Выбери ставку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🪙 50 руб", callback_data="cf_50")],
            [InlineKeyboardButton(text="🪙 100 руб", callback_data="cf_100")],
            [InlineKeyboardButton(text="🪙 250 руб", callback_data="cf_250")],
            [InlineKeyboardButton(text="🪙 500 руб", callback_data="cf_500")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="coinflip")]
        ])
    )

@dp.callback_query(lambda c: c.data.startswith("cf_") and not c.data.startswith("cf_play_"))
async def coinflip_bet(call: types.CallbackQuery):
    amount = int(call.data.split("_")[1])
    u = get_user(call.from_user.id)
    if not u or u[3] < amount:
        await call.answer("❌ Недостаточно средств! Получи бонус дня ![🎁](tg://emoji?id=6017352625983331333)")
        return

    await call.message.edit_text(
        f"🪙 **Ставка: {amount} руб**\n\n"
        f"Выбери: Орёл или Решка?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🦅 Орёл", callback_data=f"cf_play_{amount}_1")],
            [InlineKeyboardButton(text="🦅 Решка", callback_data=f"cf_play_{amount}_2")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="coinflip")]
        ])
    )

@dp.callback_query(lambda c: c.data.startswith("cf_play_"))
async def coinflip_result(call: types.CallbackQuery):
    _, _, amount_str, choice = call.data.split("_")
    amount = int(amount_str)
    choice = int(choice)
    u = get_user(call.from_user.id)
    if not u or u[3] < amount:
        await call.answer("❌ Недостаточно средств!")
        return

    result = random.randint(1, 2)
    result_text = " result = random.randint(1, 2)
    result_text = "🦅 Орёл" if result == 1 else "🦅 Решка"
    user_choice = "🦅 Орёл" if choice == 1 else "🦅 Решка"

    win = result == choice

    if win:
        cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, call.from_user.id))
        add_exp(call.from_user.id, 15)
        conn.commit()
        msg = (
            f"🎲 **Орёл & Решка**\n\n"
            f"▸ Твой выбор: {user_choice}\n"
            f"▸ Выпало: {result_text}\n"
            f"▸ Результат: **🎉 ВЫИГРЫШ! +{amount} руб**\n\n"
            f"_Удача на твоей стороне..._ 🖤"
        )
    else:
        cur.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amount, call.from_user.id))
        conn.commit()
        msg = (
            f"🎲 **Орёл & Решка**\n\n"
            f"▸ Твой выбор: {user_choice}\n"
            f"▸ Выпало: {result_text}\n"
            f"▸ Результат: **💔 Проигрыш -{amount} руб**\n\n"
            f"_Тени не прощают ошибок..._ 🖤"
        )

    await call.message.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Ещё раз", callback_data="coinflip")],
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
        f"👥 **Реферальная система**\n\n"
        f"▸ Приглашено: **{ref_count} чел**\n"
        f"▸ Заработано: **{u[4]:.0f} руб**\n\n"
        f"🔗 Твоя ссылка:\n`{ref_link}`\n\n"
        f"🔥 **Условия:**\n"
        f"▸ 20% от каждого заказа реферала\n"
        f"▸ Выплаты мгновенные\n\n"
        f"_Приведи 5 друзей — получи статус VIP_ 💎",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Забрать выплату", url="https://t.me/nezovime")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

# ----- САППОРТ -----
@dp.callback_query(lambda c: c.data == "support")
async def support(call: types.CallbackQuery):
    await call.message.edit_text(
        "📞 **Shadow Support**\n\n"
        "Связь с оператором:\n"
        "➡️ **@nezovime**\n\n"
        "🔹 Заказы\n"
        "🔹 Выплаты\n"
        "🔹 Сотрудничество\n"
        "🔹 Жалобы\n\n"
        "⏳ Среднее время ответа: 5-10 мин\n"
        "🕐 Работаем 24/7\n\n"
        "_«Мы всегда рядом, даже когда нас не видно»_ 🖤",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать", url="https://t.me/nezovime")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

# ----- НАЗАД -----
@dp.callback_query(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.edit_text(
        "🌙 **Shadow Market**\n\n"
        "👇 Выбери раздел:",
        reply_markup=main_kb()
    )

# ----- ЗАПУСК -----
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

