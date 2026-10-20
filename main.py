import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('bot_baza.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT
    )
''')
conn.commit()

def add_user(user_id, username):
    try:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

# --- BOT VA CLICK SOZLAMALARI ---
BOT_TOKEN = '8787340263:AAH73q3AYz8AY5YL3yA1DWGxItPPfhat_wk'
CLICK_TOKEN = '398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065'
ADMIN_ID = 1847219629 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- HOLATLAR ---
class AdminPanel(StatesGroup):
    xabar_kutish = State()

# --- NARXLAR LUG'ATI ---
STARS_PRICES = {
    "50": 10900 * 100,
    "75": 16350 * 100,
    "100": 21800 * 100,
    "150": 32700 * 100,
    "200": 43600 * 100,
    "250": 54500 * 100,
    "300": 65400 * 100,
    "400": 87200 * 100,
    "500": 109000 * 100,
    "750": 163500 * 100,
    "1000": 218000 * 100
}

# --- TUGMALAR (MENYULAR) ---
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌟 Stars sotib olish", callback_data="menu_stars")],
    [InlineKeyboardButton(text="💎 Premium sotib olish", callback_data="menu_premium")],
    [InlineKeyboardButton(text="👨‍💻 Admin bilan bog'lanish", callback_data="menu_admin")]
])

stars_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⭐ 50 - 10 900 so'm", callback_data="buy_50"), InlineKeyboardButton(text="⭐ 75 - 16 350 so'm", callback_data="buy_75")],
    [InlineKeyboardButton(text="⭐ 100 - 21 800 so'm", callback_data="buy_100"), InlineKeyboardButton(text="⭐ 150 - 32 700 so'm", callback_data="buy_150")],
    [InlineKeyboardButton(text="⭐ 200 - 43 600 so'm", callback_data="buy_200"), InlineKeyboardButton(text="⭐ 250 - 54 500 so'm", callback_data="buy_250")],
    [InlineKeyboardButton(text="⭐ 300 - 65 400 so'm", callback_data="buy_300"), InlineKeyboardButton(text="⭐ 400 - 87 200 so'm", callback_data="buy_400")],
    [InlineKeyboardButton(text="⭐ 500 - 109 000 so'm", callback_data="buy_500"), InlineKeyboardButton(text="⭐ 750 - 163 500 so'm", callback_data="buy_750")],
    [InlineKeyboardButton(text="⭐ 1000 - 218 000 so'm", callback_data="buy_1000")],
    [InlineKeyboardButton(text="⬅️ Orqaga (Asosiy menyu)", callback_data="back_main")]
])

premium_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💎 1 Month (Login) - 42 000 UZS", callback_data="prem_1")],
    [InlineKeyboardButton(text="💎 3 Months - 165 000 UZS", callback_data="prem_3")],
    [InlineKeyboardButton(text="💎 6 Months - 220 000 UZS", callback_data="prem_6")],
    [InlineKeyboardButton(text="💎 1 Year - 400 000 UZS", callback_data="prem_12")],
    [InlineKeyboardButton(text="⬅️ Orqaga (Asosiy menyu)", callback_data="back_main")]
])

back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Orqaga (Asosiy menyu)", callback_data="back_main")]
])

invoice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Orqaga (Bekor qilish)", callback_data="cancel_invoice")]
])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer("Salom! Telegram xizmatlari do'koniga xush kelibsiz.\nQuyidagi bo'limlardan birini tanlang:", reply_markup=main_menu)

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        users_count = len(get_all_users())
        await message.answer(f"👑 Admin panel!\n📊 Mijozlar: {users_count} ta.\nXabar yuborish uchun matn yoki rasm tashlang:")
        await state.set_state(AdminPanel.xabar_kutish)

@dp.message(AdminPanel.xabar_kutish)
async def send_broadcast(message: types.Message, state: FSMContext):
    users = get_all_users()
    count = 0
    await message.answer("⏳ Xabar yuborilmoqda...")
    for user_id in users:
        try:
            await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await message.answer(f"✅ Xabar jami {count} ta foydalanuvchiga yuborildi!")
    await state.clear()

@dp.callback_query(F.data == "menu_stars")
async def show_stars(callback: types.CallbackQuery):
    await callback.message.edit_text("Qancha yulduzcha xarid qilmoqchisiz?", reply_markup=stars_keyboard)

@dp.callback_query(F.data == "menu_premium")
async def show_premium(callback: types.CallbackQuery):
    text = (
        "💎 **Telegram Premium Pricing & Methods:**\n\n"
        "1️⃣ **Login Required (Cheaper option):**\n"
        "• Price: **42,000 UZS** per month\n"
        "*(We log into your account securely to activate).*-\n\n"
        "2️⃣ **Without Login (Gift method - Safe):**\n"
        "• **3 Months:** 165,000 UZS\n"
        "• **6 Months:** 220,000 UZS\n"
        "• **1 Year:** 400,000 UZS\n"
        "*(Sent directly as a Telegram Gift).*\n\n"
        "Buyurtma berish uchun quyidagi tugmalardan birini bosing:"
    )
    await callback.message.edit_text(text, reply_markup=premium_keyboard, parse_mode="Markdown")

# --- PREMIUM TUGMALARI BOSILGANDA ---
@dp.callback_query(F.data.startswith("prem_"))
async def process_premium_buy(callback: types.CallbackQuery):
    plan = callback.data.split("_")[1]
    
    if plan == "1":
        plan_name = "1 Month (Login Required) - 42 000 UZS"
    elif plan == "3":
        plan_name = "3 Months - 165 000 UZS"
    elif plan == "6":
        plan_name = "6 Months - 220 000 UZS"
    elif plan == "12":
        plan_name = "1 Year - 400 000 UZS"
    else:
        plan_name = "Telegram Premium"

    # Mijozning username'i bormi-yo'qligini tekshiramiz
    user = callback.from_user
    if user.username:
        user_link = f"@{user.username}"
    else:
        # Username bo'lmasa ismini bosiladigan ssilka qilamiz
        user_link = f"<a href='tg://user?id={user.id}'>{user.first_name}</a> (Username yo'q)"

    # Adminga xabar yuborish
    admin_text = (
        f"💎 YANGI PREMIUM BUYURTMA!\n"
        f"👤 Mijoz: {user_link}\n"
        f"🆔 ID: {user.id}\n"
        f"📦 Reja: {plan_name}\n"
        f"Mijoz bilan bog'lanib, to'lov va faollashtirishni amalga oshiring!"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")

    # Mijozga javob
    await callback.message.edit_text(
        f"✅ Siz **{plan_name}** tanladingiz!\n\n"
        f"Buyurtmangiz adminga yuborildi. Admin tez orada siz bilan bog'lanadi (@wrlpsew).\n"
        f"Telefon: +998930657103",
        reply_markup=back_keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "menu_admin")
async def show_admin_contact(callback: types.CallbackQuery):
    await callback.message.edit_text("Savol yoki muammolar bo'yicha adminga murojaat qiling:\n\n👨‍💻 Admin: @wrlpsew\n📞 Tel: +998930657103", reply_markup=back_keyboard)

@dp.callback_query(F.data == "back_main")
async def go_back_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Quyidagi bo'limlardan birini tanlang:", reply_markup=main_menu)

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    price_tiyin = STARS_PRICES[amount]
    await callback.message.delete()
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"⭐ {amount} ta Telegram Stars",
        description=f"{amount} ta Telegram yulduzchasini xarid qilish uchun to'lov.",
        payload=f"stars_{amount}",
        provider_token=CLICK_TOKEN,
        currency="UZS",
        prices=[LabeledPrice(label=f"{amount} Stars", amount=price_tiyin)],
        start_parameter="stars_payment",
        reply_markup=invoice_keyboard
    )

@dp.callback_query(F.data == "cancel_invoice")
async def process_cancel_invoice(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("❌ Xarid bekor qilindi.\nQuyidagi bo'limlardan birini tanlang:", reply_markup=main_menu)

@dp.pre_checkout_query()
async def pre_checkout_process(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment_process(message: types.Message):
    amount = message.successful_payment.invoice_payload.split("_")[1]
    user = message.from_user
    if user.username:
        user_link = f"@{user.username}"
    else:
        user_link = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    admin_text = (f"✅ YANGI TO'LOV (CLICK)!\n"
                  f"👤 Mijoz: {user_link}\n"
                  f"🆔 ID: {user.id}\n"
                  f"💰 Xarid qildi: {amount} Stars\n"
                  f"To'lov muvaffaqiyatli o'tdi. Mijozga yulduzchalarni tashlab bering!")
    await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
    await message.answer("✅ To'lovingiz qabul qilindi!\nTez orada adminga xabar boradi va yulduzchalar profilingizga yuboriladi.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.set_my_commands([
        BotCommand(command="start", description="Asosiy menyu"),
        BotCommand(command="admin", description="Admin panel")
    ])
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
                   
