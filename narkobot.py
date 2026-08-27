import asyncio
import random
import datetime
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ===== НАСТРОЙКИ =====
TOKEN = "8374980332:AAEuIe139BhI0JBrX8c0fpqmjPET4nA0PKU"   
ADMIN_ID = 5663913815                    # твой Telegram ID
CHANNEL_ID = 0             # ID канала-витрины (если есть)
SUPPORT_USERNAME = "nezovime"   # юзернейм саппорта (без @)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== ТОВАРЫ =====
PRODUCTS = {
    "1": {
        "name": "🧊 Кристаллы (MDPV)",
        "price": "3 500 ₽/г",
        "desc": "Чистые кристаллы. Заводская упаковка. Эффект: 4-6 ч.",
        "stock": "15 г",
        "image": "ice.jpg"
    },
    "2": {
        "name": "🌿 Шишки (Amnesia Haze)",
        "price": "2 000 ₽/г",
        "desc": "Топовый сорт. Ароматный, бодрящий. Indoor.",
        "stock": "25 г",
        "image": "weed.jpg"
    },
    "3": {
        "name": "💊 MDMA (кристаллы)",
        "price": "2 500 ₽/г",
        "desc": "Чистый MDMA. Продажа от 0.5 г. Тест-кит в подарок.",
        "stock": "10 г",
        "image": "mdma.jpg"
    },
    "4": {
        "name": "❄️ Кокаин (Colombia)",
        "price": "7 000 ₽/г",
        "desc": "Белый, чистый. Чили-флейк. Быстрая доставка.",
        "stock": "8 г",
        "image": "coke.jpg"
    },
    "5": {
        "name": "![🔴](tg://emoji?id=6017204539805932704) Alpha-PVP (соль)",
        "price": "2 800 ₽/г",
        "desc": "Кристаллическая соль. Мощный эффект. Проверено.",
        "stock": "20 г",
        "image": "alpha.jpg"
    },
    "6": {
        "name": "💜 Мефедрон (кристаллы)",
        "price": "2 200 ₽/г",
        "desc": "Чистый меф. Белые/светло-бежевые кристаллы.",
        "stock": "30 г",
        "image": "meph.jpg"
    },
    "7": {
        "name": "🧪 LSD (марки)",
        "price": "1 500 ₽/шт",
        "desc": "Кислота 200 мкг. Блоттеры. Рисунки: Глаз, Звёзды.",
        "stock": "50 шт",
        "image": "lsd.jpg"
    },
    "8": {
        "name": "💊 Ксанакс (Alprazolam)",
        "price": "3 000 ₽/10 таб",
        "desc": "Аптечный. Фирменная упаковка. 1 мг.",
        "stock": "40 упаковок",
        "image": "xanax.jpg"
    }
}

# ===== КОРЗИНА (in-memory, временно) =====
carts = {}

# ===== КОМАНДЫ =====
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    user_id = msg.from_user.id
    carts[user_id] = []
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 Каталог", callback_data="catalog")
    kb.button(text="🛒 Корзина", callback_data="cart")
    kb.button(text="❓ Инфо", callback_data="info")
    kb.button(text="![📞](tg://emoji?id=6016903402468940975) Саппорт", url=f"https://t.me/{SUPPORT_USERNAME}")
    kb.adjust(2)
    
    text = (
        "🌀 <b>НаркоМаркет</b> 🌀\n\n"
        "🔐 Только проверенные позиции\n"
        "🚚 Анонимная доставка по РФ\n"
        "![⚡️](tg://emoji?id=6014627855781076391) Оплата: BTC / USDT / Наличные\n\n"
        "![📌](tg://emoji?id=6017218803392323084) <b>Правила:</b>\n"
        "• Минимальный заказ: 1 000 ₽\n"
        "• Работаем круглосуточно\n"
        "• Вес +/- 0.05 г (погрешность)\n\n"
        "👇 Выбери действие:"
    )
    
    await msg.answer(text, reply_markup=kb.as_markup())

# ===== КАТАЛОГ =====
@dp.callback_query(lambda c: c.data == "catalog")
async def show_catalog(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    for pid, p in PRODUCTS.items():
        kb.button(text=f"{p['name']} — {p['price']}", callback_data=f"prod_{pid}")
    kb.button(text="🛒 Корзина", callback_data="cart")
    kb.button(text="🔙 Назад", callback_data="back_main")
    kb.adjust(1)
    
    await call.message.edit_text(
        "📋 <b>КАТАЛОГ ТОВАРОВ</b>\n\n"
        "Выбери позицию для просмотра:",
        reply_markup=kb.as_markup()
    )

# ===== КАРТОЧКА ТОВАРА =====
@dp.callback_query(lambda c: c.data.startswith("prod_"))
async def product_card(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]
    
    kb = InlineKeyboardBuilder()
    kb.button(text=f"![➕](tg://emoji?id=6017367830167559319) Добавить 0.5 г", callback_data=f"add_{pid}_05")
    kb.button(text=f"![➕](tg://emoji?id=6017367830167559319) Добавить 1 г", callback_data=f"add_{pid}_1")
    kb.button(text=f"![➕](tg://emoji?id=6017367830167559319) Добавить 2 г", callback_data=f"add_{pid}_2")
    kb.button(text=f"![➕](tg://emoji?id=6017367830167559319) Своё количество", callback_data=f"custom_{pid}")
    kb.button(text="🛒 В корзину", callback_data=f"add_{pid}_1")
    kb.button(text="🔙 В каталог", callback_data="catalog")
    kb.adjust(2, 2, 1, 1)
    
    text = (
        f"<b>{p['name']}</b>\n\n"
        f"![📝](tg://emoji?id=6017137473891605745) <b>Описание:</b>\n{p['desc']}\n\n"
        f"💰 <b>Цена:</b> {p['price']}\n"
        f"📦 <b>В наличии:</b> {p['stock']}\n\n"
        f"![✅](tg://emoji?id=6016835129668803369) 100% качество\n"
        f"![✅](tg://emoji?id=6016835129668803369) Анонимно и безопасно\n"
        f"![✅](tg://emoji?id=6016835129668803369) Доставка по всей РФ\n\n"
        f"Выбери количество:"
    )
    
    await call.message.edit_text(text, reply_markup=kb.as_markup())

# ===== ДОБАВЛЕНИЕ В КОРЗИНУ =====
@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    parts = call.data.split("_")
    pid = parts[1]
    amount_str = parts[2]
    
    if pid in ["05", "1", "2"]:
        pid, amount_str = amount_str, parts[2]
    
    amount = amount_str
    p = PRODUCTS[pid]
    user_id = call.from_user.id
    
    if user_id not in carts:
        carts[user_id] = []
    
    # Проверяем, есть ли уже такой товар в корзине
    found = False
    for item in carts[user_id]:
        if item["pid"] == pid and item["amount"] == amount:
            item["qty"] += 1
            found = True
            break
    
    if not found:
        carts[user_id].append({
            "pid": pid,
            "name": p["name"],
            "price": p["price"],
            "amount": amount,
            "qty": 1
        })
    
    await call.answer(f"![✅](tg://emoji?id=6016835129668803369) {p['name']} ({amount}) добавлен в корзину", show_alert=False)

# ===== КОРЗИНА =====
@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    items = carts.get(user_id, [])
    
    if not items:
        kb = InlineKeyboardBuilder()
        kb.button(text="📋 В каталог", callback_data="catalog")
        kb.button(text="🔙 Назад", callback_data="back_main")
        
        await call.message.edit_text(
            "🛒 <b>Корзина пуста</b>\n\nДобавь товары из каталога!",
            reply_markup=kb.as_markup()
        )
        return
    
    total = 0
    text = "🛒 <b>ТВОЯ КОРЗИНА</b>\n\n"
    i = 1
    for item in items:
        price_val = int(item["price"].replace(" ", "").replace("₽", "").split("/")[0].split(".")[0])
        total += price_val * item["qty"]
        text += f"{i}. {item['name']} — {item['amount']} × {item['qty']} = {price_val * item['qty']:,} ₽\n".replace(",", " ")
        i += 1
    
    text += f"\n![💵](tg://emoji?id=6014619815602298851) <b>ИТОГО: {total:,} ₽</b>\n".replace(",", " ")
    text += "\n![💳](tg://emoji?id=6016901577107839515) Оплата: BTC / USDT / Наличные"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="![✅](tg://emoji?id=6016835129668803369) Оформить заказ", callback_data="checkout")
    kb.button(text="![🗑](tg://emoji?id=6014972359402855259) Очистить корзину", callback_data="clear_cart")
    kb.button(text="📋 Каталог", callback_data="catalog")
    kb.adjust(1, 1, 1)
    
    await call.message.edit_text(text, reply_markup=kb.as_markup())

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    carts[call.from_user.id] = []
    await call.answer("![🗑](tg://emoji?id=6014972359402855259) Корзина очищена")
    await show_cart(call)

# ===== ОФОРМЛЕНИЕ ЗАКАЗА =====
@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    user_id = call.from_user.id
    items = carts.get(user_id, [])
    
    if not items:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    order_id = f"NARKO-{random.randint(10000, 99999)}"
    
    # Собираем текст заказа
    total = 0
    order_text = f"🔖 <b>ЗАКАЗ #{order_id}</b>\n\n"
    for item in items:
        price_val = int(item["price"].replace(" ", "").replace("₽", "").split("/")[0].split(".")[0])
        total += price_val * item["qty"]
        order_text += f"• {item['name']} ({item['amount']}) × {item['qty']}\n"
    
    order_text += f"\n![💵](tg://emoji?id=6014619815602298851) <b>Сумма: {total:,} ₽</b>\n".replace(",", " ")
    
    # Реквизиты BTC/USDT
    btc_addr = "bc1qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    usdt_addr = "0xXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="![💳](tg://emoji?id=6016901577107839515) Я оплатил (BTC)", callback_data=f"paid_btc_{order_id}")
    kb.button(text="![💳](tg://emoji?id=6016901577107839515) Я оплатил (USDT)", callback_data=f"paid_usdt_{order_id}")
    kb.button(text="![💵](tg://emoji?id=6014619815602298851) Наличными (Москва)", callback_data=f"paid_cash_{order_id}")
    kb.button(text="❌ Отменить", callback_data="catalog")
    kb.adjust(1, 1, 1, 1)
    
    payment_text = (
        f"{order_text}\n\n"
        f"![💳](tg://emoji?id=6016901577107839515) <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ:</b>\n\n"
        f"![₿](tg://emoji?id=6015095646439088225) <b>Bitcoin (BTC):</b>\n"
        f"<code>{btc_addr}</code>\n\n"
        f"![💎](tg://emoji?id=6016882537517818399) <b>USDT (ERC-20):</b>\n"
        f"<code>{usdt_addr}</code>\n\n"
        f"💰 <b>Или наличными по Москве:</b>\n"
        f"Самовывоз/встреча по предзаказу\n\n"
        f"![📌](tg://emoji?id=6017218803392323084) <b>После оплаты нажми соответствующую кнопку</b>\n"
        f"![⏳](tg://emoji?id=6016961981527897114) Обработка: до 30 мин"
    )
    
    await call.message.edit_text(payment_text, reply_markup=kb.as_markup())
    
    # Отправляем админу уведомление
    user_info = f"@{call.from_user.username or 'нет юзернейма'} | ID: {user_id}"
    await bot.send_message(
        ADMIN_ID,
        f"🆕 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
        f"Номер: #{order_id}\n"
        f"Клиент: {user_info}\n"
        f"Сумма: {total:,} ₽\n".replace(",", " ") +
        f"Товары:\n" +
        "\n".join([f"• {i['name']} ({i['amount']}) × {i['qty']}" for i in items]) +
        f"\n\n![⏳](tg://emoji?id=6016961981527897114) Ожидание оплаты..."
    )

# ===== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ =====
@dp.callback_query(lambda c: c.data.startswith("paid_"))
async def confirm_payment(call: types.CallbackQuery):
    parts = call.data.split("_")
    method = parts[1]  # btc, usdt, cash
    order_id =parts[2] if len(parts) > 2 else f"NK-{random.randint(10000, 99999)}"
    
    method_names = {"btc": "Bitcoin (BTC)", "usdt": "USDT (ERC-20)", "cash": "Наличные (Москва)"}
    method_name = method_names.get(method, method)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Статус заказа", callback_data=f"status_{order_id}")
    kb.button(text="📞 Саппорт", url=f"https://t.me/{SUPPORT_USERNAME}")
    kb.button(text="📋 В каталог", callback_data="catalog")
    kb.adjust(1, 1, 1)
    
    await call.message.edit_text(
        f"✅ <b>Оплата принята!</b>\n\n"
        f"Заказ: #{order_id}\n"
        f"Метод: {method_name}\n\n"
        f"⏳ <b>Статус: Ожидает проверки</b>\n\n"
        f"🕐 Оператор проверит платёж в течение 30 минут.\n"
        f"После подтверждения ты получишь:\n"
        f"📍 Адрес закладки / контакт курьера\n\n"
        f"❓ Вопросы — в саппорт: @{SUPPORT_USERNAME}",
        reply_markup=kb.as_markup()
    )
    
    # Уведомление админу
    user_info = f"@{call.from_user.username or 'нет юзернейма'} | ID: {call.from_user.id}"
    await bot.send_message(
        ADMIN_ID,
        f"💰 <b>ПЛАТЁЖ ОЖИДАЕТ ПРОВЕРКИ</b>\n\n"
        f"Заказ: #{order_id}\n"
        f"Метод: {method_name}\n"
        f"Клиент: {user_info}\n\n"
        f"⏳ Проверь вручную и подтверди или отклони."
    )

# ===== СТАТУС ЗАКАЗА =====
@dp.callback_query(lambda c: c.data.startswith("status_"))
async def order_status(call: types.CallbackQuery):
    order_id = call.data.split("_")[1]
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Обновить статус", callback_data=f"status_{order_id}")
    kb.button(text="📞 Саппорт", url=f"https://t.me/{SUPPORT_USERNAME}")
    
    statuses = ["🔴 Ожидает оплаты", "🟡 Проверка платежа", "🟢 В обработке", "🔵 Отправлен", "✅ Выдан/доставлен"]
    random_status = random.choice(statuses[1:3])  # симуляция
    
    await call.message.edit_text(
        f"📦 <b>Статус заказа #{order_id}</b>\n\n"
        f"Текущий статус: {random_status}\n\n"
        f"🕐 Последнее обновление: {datetime.datetime.now().strftime('%H:%M %d.%m')}\n\n"
        f"Подробности: ожидайте, оператор обрабатывает заказ.",
        reply_markup=kb.as_markup()
    )

# ===== ИНФО =====
@dp.callback_query(lambda c: c.data == "info")
async def show_info(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Оплата", callback_data="payment_info")
    kb.button(text="🚚 Доставка", callback_data="delivery_info")
    kb.button(text="🔒 Анонимность", callback_data="anon_info")
    kb.button(text="🔙 Назад", callback_data="back_main")
    kb.adjust(2, 1, 1)
    
    await call.message.edit_text(
        "❓ <b>ИНФОРМАЦИЯ</b>\n\n"
        "Выбери раздел:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "payment_info")
async def payment_info(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="info")
    
    await call.message.edit_text(
        "💳 <b>ОПЛАТА</b>\n\n"
        "Принимаем:\n"
        "₿ Bitcoin (BTC) — анонимно\n"
        "💎 USDT (ERC-20/TRC-20) — быстро\n"
        "💵 Наличные — по Москве/СПб\n\n"
        "⚠️ Не принимаем:\n"
        "❌ Карты РФ (Сбер, Тинькофф)\n"
        "❌ QIWI, ЮMoney\n"
        "❌ Переводы по номеру телефона\n\n"
        "Связано с безопасностью твоей и нашей.",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "delivery_info")
async def delivery_info(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="info")
    
    await call.message.edit_text(
        "🚚 <b>ДОСТАВКА</b>\n\n"
        "📍 <b>Москва/СПб:</b>\n"
        "• Закладка в течение 2-4 ч после оплаты\n"
        "• Встреча с курьером — по договорённости\n\n"
        "🌍 <b>РФ (остальные города):</b>\n"
        "• Почта России — 5-10 дней\n"
        "• СДЭК — 3-7 дней\n"
        "• Транспортные компании\n\n"
        "⚠️ За утерю почтой не отвечаем,\n"
        "но делаем скидку 50% на повторный заказ",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "anon_info")
async def anon_info(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="info")
    
    await call.message.edit_text(
        "🔒 <b>АНОНИМНОСТЬ</b>\n\n"
        "Мы гарантируем:\n"
        "✅ Полная конфиденциальность\n"
        "✅ Чистые сим-карты для связи\n"
        "✅ Криптовалюта — неотслеживаемо\n"
        "✅ Закладки в случайных местах\n"
        "✅ Уничтожение переписки после заказа\n\n"
        "⚠️ Наша рекомендация:\n"
        "• Используй VPN/TOR\n"
        "• Не храни переписку\n"
        "• Не указывай настоящие данные\n\n"
        "Твоя безопасность — наш приоритет.",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "back_main")
async def back_main(call: types.CallbackQuery):
    await start_cmd(call.message)

# ===== АДМИН-ПАНЕЛЬ =====
@dp.message(Command("admin"))
async def admin_panel(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔️ Доступ запрещён")
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Статистика", callback_data="admin_stats")
    kb.button(text="📋 Все заказы", callback_data="admin_orders")
    kb.button(text="➕ Добавить товар", callback_data="admin_add")
    kb.button(text="✏️ Изменить товар", callback_data="admin_edit")
    kb.button(text="📢 Сделать рассылку", callback_data="admin_mail")
    kb.adjust(1)
    
    await msg.answer(
        "⚙️ <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        "Управление магазином:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("⛔️")
    
    total_orders = random.randint(50, 200)
    today_orders = random.randint(3, 15)
    total_revenue = random.randint(50000, 500000)
    
    await call.message.edit_text(
        "📊 <b>СТАТИСТИКА</b>\n\n"
        f"📦 Всего заказов: {total_orders}\n"
        f"📦 За сегодня: {today_orders}\n"
        f"💰 Общая выручка: {total_revenue:,} ₽\n".replace(",", " ") +
        f"👥 Активных пользователей: {random.randint(20, 100)}\n"
        f"📋 Товаров в каталоге: {len(PRODUCTS)}\n\n"
        f"<i>Данные обновляются автоматически</i>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙", callback_data="admin")]]
        )
    )

@dp.callback_query(lambda c: c.data == "admin")
async def admin_back(call: types.CallbackQuery):
    await admin_panel(call.message)

# ===== ЗАПУСК =====
async def main():
    print("🚀 НаркоБот запущен!")
    print(f"📋 Товаров: {len(PRODUCTS)}")
    print(f"👤 Admin ID: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
