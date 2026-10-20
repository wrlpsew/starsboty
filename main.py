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
async def cmd_start(
    
