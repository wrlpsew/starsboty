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

cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
''')
conn.commit()

cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('discount', '0')")
conn.commit()

def set_discount(percent: int):
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'discount'", (str(percent),))
    conn.commit()

def get_discount() -> int:
    cursor.execute("SELECT value FROM settings WHERE key = 'discount'")
    row = cursor.fetchone()
    return int(row[0]) if row else 0

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

# --- STARS ASL NARXLARI ---
BASE_STARS_PRICES = {
    "50": 10900,
    "75": 16350,
    "100": 21800,
    "150": 32700,
    "200": 43600,
    "250": 54500,
    "300": 65400,
    "400": 87200,
    "500": 109000,
    "750": 163500,
    "1000": 218000
}

def calculate_price(amount_str: str) -> int:
    base_price = BASE_STARS_PRICES[amount_str]
    discount = get_discount()
    final_price = base_price * (100 - discount) / 100
    return int(final_price * 100)

def get_stars_keyboard():
    discount = get_discount()
    kb = []
    keys = list(BASE_STARS_PRICES.keys())
    for i in range(0, len(keys), 2):
        row = []
        for j in range(2):
            if i + j < len(keys):
                amt = keys[i + j]
                original = BASE_STARS_PRICES[amt]
                current = int(original * (100 - discount) / 100)
                
                if discount > 0:
                    text = f"⭐ {amt} - ~{original:,}~ {current:,} so'm 🔥"
                else:
                    text = f"⭐ {amt} - {current:,} so'm"
                
                row.append(InlineKeyboardButton(text=text, callback_data=f"buy_{amt}"))
        kb.append(row)
        
    kb.append([InlineKeyboardButton(text="⬅️ Orqaga (Asosiy menyu)", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ASOSIY MENYU ---
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌟 Telegram Stars", callback_data="menu_stars")],
    [InlineKeyboardButton(text="💎 Telegram Premium", callback_data="menu_premium")],
    [InlineKeyboardButton(text="👨‍💻 Admin bilan bog'lanish", callback_data="menu_admin")]
])

# PREMIUM BO'LIMI MENYUSI (Alohida)
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

# Admin uchun chegirma tanlash tugmalari
def get_admin_keyboard():
    current = get_discount()
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{'✅ ' if current==5 else ''}5%", callback_data="set_disc_5"),
            InlineKeyboardButton(text=f"{'✅ ' if current==10 else ''}10%", callback_data="set_disc_10"),
            InlineKeyboardButton(text=f"{'✅ ' if current==20 else ''}20%", callback_data="set_disc_20"),
            InlineKeyboardButton(text=f"{'✅ ' if current==30 else ''}30%", callback_data="set_disc_30")
        ],
        [
            InlineKeyboardButton(text=f"{'✅ ' if current==0 else ''}❌ Chegirmani o'chirish (0%)", callback_data="set_disc_0")
        ]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer("Salom! Telegram xizmatlari do'koniga xush kelibsiz.\nQuyidagi bo'limlardan birini tanlang:", reply_markup=main_menu)

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.clear()
        users_count = len(get_all_users())
        current_disc = get_discount()
        text = (
            f"👑 **Admin panel!**\n"
            f"📊 Mijozlar: {users_count} ta\n"
            f"🔥 Stars bo'yicha hozirgi chegirma: **{current_disc}%**\n\n"
            f"👇 Chegirma foizini tanlang yoki xabar yuborish uchun matn/rasm tashlang:"
        )
        await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("set_disc_"))
async def process_set_discount_callback(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        percent = int(callback.data.split("_")[2])
        set_discount(percent)
        current_disc = get_discount()
        users_count = len(get_all_users())
        
        text = (
            f"👑 **Admin panel!**\n"
            f"📊 Mijozlar: {users_count} ta\n"
            f"🔥 Stars bo'yicha hozirgi chegirma: **{current_disc}%** (Muvaffaqiyatli o'rnatildi! ✅)\n\n"
            f"👇 Chegirma foizini tanlang yoki xabar yuborish uchun matn/rasm tashlang:"
        )
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
        await callback.answer(f"Chegirma {percent}% ga o'zgartirildi!")

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

# --- STARS BO'LIMI ---
@dp.callback_query(F.data == "menu_stars")
async def show_stars(callback: types.CallbackQuery):
    disc = get_discount()
    text = f"🌟 **Telegram Stars (Yulduzchalar) bo'limi**\n\nHozirgi chegirma: **{disc}%**\nKerakli miqdorni tanlang:"
    await callback.message.edit_text(text, reply_markup=get_stars_keyboard(), parse_mode="Markdown")

# --- PREMIUM BO'LIMI ---
@dp.callback_query(F.data == "menu_premium")
async def show_premium(callback: types.CallbackQuery):
    text = (
        "💎 **Telegram Premium bo'limi & Shartlari:**\n\n"
        "1️⃣ **Login Required (Arzonroq variant):**\n"
        "• Narxi: **42,000 UZS** (1 oylik)\n"
        "*(Faollashtirish uchun profilingizga qisqa muddatga kiriladi).*-\n\n"
        "2️⃣ **Without Login (Sovg'a usuli - Xavfsiz):**\n"
        "• **3 Oylik:** 165,000 UZS\n"
        "• **6 Oylik:** 220,000 UZS\n"
        "• **1 Yillik:** 400,000 UZS\n"
        "*(Telegram orqali to'g'ridan-to'g'ri Gift qilib yuboriladi).*\n\n"
        "Kerakli muddatni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=premium_keyboard, parse_mode="Markdown")

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

    user = callback.from_user
    if user.username:
        user_link = f"@{user.username}"
    else:
        user_link = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    admin_text = (
        f"💎 YANGI PREMIUM BUYURTMA!\n"
        f"👤 Mijoz: {user_link}\n"
        f"🆔 ID: {user.id}\n"
        f"📦 Reja: {plan_name}\n"
        f"Mijoz bilan bog'lanib, to'lov va faollashtirishni amalga oshiring!"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")

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
    price_tiyin = calculate_price(amount)
    
    base_val = BASE_STARS_PRICES[amount]
    disc = get_discount()
    curr_val = int(base_val * (100 - disc) / 100)

    await callback.message.delete()
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"⭐ {amount} ta Telegram Stars",
        description=f"{amount} ta yulduzcha xaridi (Chegirma: {disc}%).",
        payload=f"stars_{amount}",
        provider_token=CLICK_TOKEN,
        currency="UZS",
        prices=[LabeledPrice(label=f"{amount} Stars ({curr_val:,} so'm)", amount=price_tiyin)],
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
