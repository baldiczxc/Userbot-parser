# ---------------------------
# Import Telegram Api Handler For KeyBoards
# ---------------------------
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

async def start_cl():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    menu = KeyboardButton("Меню 🏠")
    kb.row(menu)
    return kb

async def menu_cl():
    kb = InlineKeyboardMarkup()
    chats = InlineKeyboardButton(text="🛠 Чаты", callback_data="chats")
    settings = InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
    stats = InlineKeyboardButton(text="📊 Статистика", callback_data="stats")

    kb.row(chats, stats)
    kb.row(settings)

    return kb

async def chat_types_cb():
    kb = InlineKeyboardMarkup()
    groups = InlineKeyboardButton(text="✏️ Группы", callback_data="chats_groups")
    channels = InlineKeyboardButton(text="📰 Каналы", callback_data="chats_channels")
    back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")

    kb.row(groups, channels)
    kb.row(back)

    return kb

async def chan_back_cb():
    kb = InlineKeyboardMarkup()
    back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_channels")

    kb.row(back)

    return kb

async def grop_back_cb():
    kb = InlineKeyboardMarkup()
    back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_groups")

    kb.row(back)

    return kb

async def stats_back_cb():
    kb = InlineKeyboardMarkup()
    export = InlineKeyboardButton(text="🔰 Экспорт статистики xlsx", callback_data="export")
    back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")

    kb.row(export)
    kb.row(back)

    return kb
