# ---------------------------
# Import Telegram Api Handler For KeyBoards
# ---------------------------
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import get_user_ktu_own


# ---------------------------
# Create Keyboard For Menu
# ---------------------------
async def start_cl():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    menu = KeyboardButton("Меню 🏠")
    sup = KeyboardButton("Поддержка 🆘")

    kb.row(menu)
    kb.row(sup)

    return kb

async def menu_cl():
    kb = InlineKeyboardMarkup()
    usb = InlineKeyboardButton(text=f"🗂 Католог", callback_data="userbot_sell")
    profile = InlineKeyboardButton(text=f"👤 Профиль", callback_data="profile")
    usbs = InlineKeyboardButton(text=f"👾 Мои user-bot", callback_data="us_usb")

    kb.row(usb)
    kb.row(profile, usbs)

    return kb

async def recovery_cl():
    kb = InlineKeyboardMarkup()
    usb = InlineKeyboardButton(text=f"❇️ Восстановить аккаунт", callback_data="recovery")
    kb.row(usb)
    return kb


async def cancel_stat_cl():
    kb = InlineKeyboardMarkup()
    usb = InlineKeyboardButton(text=f"❌ Отмена", callback_data="cancel_stat")
    kb.row(usb)
    return kb

async def usb_cl():
    kb = InlineKeyboardMarkup()
    red = InlineKeyboardButton(text=f"✏️ Изменить:", callback_data="None")
    red_id = InlineKeyboardButton(text=f"Api ID", callback_data="red_id")
    red_hash = InlineKeyboardButton(text=f"Api Hash", callback_data="red_hash")
    red_tk = InlineKeyboardButton(text=f"Bot Token", callback_data="red_tk")
    red_phn = InlineKeyboardButton(text=f"Phone Number", callback_data="red_phn")
    usbs = InlineKeyboardButton(text=f"🔙 Назад", callback_data="us_usb")
    own = InlineKeyboardButton(text=f"🌀 Управление:", callback_data="None")
    own_stp = InlineKeyboardButton(text=f"⏹️", callback_data="stop_usb")
    own_res = InlineKeyboardButton(text=f"🔄", callback_data="restart_usb")
    own_str = InlineKeyboardButton(text=f"▶️", callback_data="start_usb")
    kb.row(red)
    kb.row(red_id, red_hash)
    kb.row(red_tk, red_phn)
    kb.row(own)
    kb.row(own_stp, own_res, own_str)
    kb.row(usbs)

    return kb

async def my_usb_cl():
    kb = InlineKeyboardMarkup()
    usb_name = "KTU-Bot"
    usb = InlineKeyboardButton(text=f"[👾] {usb_name}", callback_data="ktubot")
    back = InlineKeyboardButton(text=f"🔙 Назад", callback_data="back_to_menu")
    kb.row(usb)
    kb.row(back)

    return kb


async def buy_cl():
    kb = InlineKeyboardMarkup()
    usb_name = "KTU-Bot | 1 TON"
    usb = InlineKeyboardButton(text=f"[👾] {usb_name}", callback_data="userbots")
    back = InlineKeyboardButton(text=f"🔙 Назад", callback_data="back_to_menu")
    kb.row(usb)
    kb.row(back)

    return kb

async def profile_cl():
    kb = InlineKeyboardMarkup()
    usb = InlineKeyboardButton(text=f"💵 Пополнить баланс", callback_data="pay_bal")
    back = InlineKeyboardButton(text=f"🔙 Назад", callback_data="back_to_menu")
    kb.row(usb)
    kb.row(back)

    return kb

async def buy_KTU_cl(chat_id):
    check_own = await get_user_ktu_own(chat_id)

    kb = InlineKeyboardMarkup()

    bl = InlineKeyboardButton(text=f"💎 CryptoBot", callback_data="pay_invoice")
    cb = InlineKeyboardButton(text=f"💰 С баланса", callback_data="pay_balance")
    back = InlineKeyboardButton(text=f"🔙 Назад", callback_data="back_to_catalog")
    buy = InlineKeyboardButton(text=f"✅ Куплен", callback_data="None")

    if check_own:
        kb.row(buy)
        kb.row(back)
    else:
        kb.row(bl)
        kb.row(cb)
        kb.row(back)
    return kb


async def buy_KTU_bal_cl():
    kb = InlineKeyboardMarkup()

    cb = InlineKeyboardButton(text=f"💸 Оплатить", callback_data="paid_balance")
    back = InlineKeyboardButton(text=f"🔙 Назад", callback_data="userbots")

    kb.row(cb)
    kb.row(back)

    return kb

async def pay_up_bal_cl():
    kb = InlineKeyboardMarkup()
    a = InlineKeyboardButton(text=f"1 TON", callback_data="pay_a")
    b = InlineKeyboardButton(text=f"2 TON", callback_data="pay_b")
    c = InlineKeyboardButton(text=f"3 TON", callback_data="pay_c")
    d = InlineKeyboardButton(text=f"4 TON", callback_data="pay_d")
    e = InlineKeyboardButton(text=f"5 TON", callback_data="pay_e")
    f = InlineKeyboardButton(text=f"10 TON", callback_data="pay_f")
    back = InlineKeyboardButton(text=f"🔙 Назад", callback_data="back_to_profile")

    kb.row(a, b, c)
    kb.row(d, e, f)
    kb.row(back)

    return kb

async def backup_cl():
    kb = InlineKeyboardMarkup()

    backup = InlineKeyboardButton(text="[🆘] Восстановить", callback_data="settings")

    kb.row(backup)

    return kb

async def usb_cb():
    kb = InlineKeyboardMarkup()

    marks = InlineKeyboardButton(text="🧷 Маркеры", callback_data="settings")

    kb.row(marks)

    return kb


