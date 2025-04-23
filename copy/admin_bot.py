from pyrogram.filters import channel
from io import BytesIO
from config import admin_id, bot_token
from database import *
from keyboards import *
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
import pandas as pd

bot = Bot(bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class MarkState(StatesGroup):
    waiting_for_mark = State()

async def check_is_admin(chat_id):
    adm_id = await get_user_admin_id(chat_id)
    return True if adm_id == admin_id else False

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    chat_id = msg.chat.id
    if not await check_is_admin(chat_id):
        return
    await bot.send_message(chat_id, "Добро пожаловать в вашего <b>личного бота</b> для Управления юзерботом <b>KTU-Bot</b>", reply_markup=await start_cl(), parse_mode="HTML")

@dp.message_handler(lambda message: message.text == "Меню 🏠")
async def menu_handler(msg: types.Message):
    await show_main_menu(msg)

async def show_main_menu(msg):
    chat_id = msg.chat.id
    if not await check_is_admin(chat_id):
        return

    await bot.send_message(chat_id, "Выберите интересующюю вас функцию:", reply_markup=await menu_cl())

@dp.callback_query_handler(lambda c: c.data == 'chats' or c.data == 'back_to_chats')
async def userbots_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    await bot.edit_message_text("Выберите тип чатов:", chat_id, message_id, reply_markup=await chat_types_cb())


@dp.callback_query_handler(lambda c: c.data == 'export')
async def userbots_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_chats = await get_user_chats_from_db(chat_id, chat_type="groups")
    channel_chats = await get_user_chats_from_db(chat_id, chat_type="channels")
    supergroup_chats = await get_user_chats_from_db(chat_id, chat_type="supergroups")

    # Объединяем все чаты в один список и удаляем дубликаты по 'id'
    all_chats = user_chats + supergroup_chats + channel_chats
    unique_chats = {chat['id']: chat for chat in all_chats}.values()  # Используем ID как ключ для уникальности

    # Преобразуем чаты в таблицу (DataFrame)
    data = []
    for chat in unique_chats:
        chat_id = chat['id']
        title = chat['title'] if isinstance(chat['title'], str) else chat['title'].get('title', 'Без названия')
        data.append([chat_id, title])

    # Создаем DataFrame из полученных данных
    df = pd.DataFrame(data, columns=["Chat ID", "Title"])

    # Сохраняем DataFrame в Excel
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    # Отправляем файл пользователю
    await bot.send_document(
        chat_id=callback_query.from_user.id,
        document=output,
        caption="user_chats.xlsx",  # Добавляем имя файла в описание
        filename="user_chats.xlsx",  # Указываем имя файла в параметре filename
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # Указываем MIME тип
    )


@dp.callback_query_handler(lambda c: c.data == 'back_to_channels' or c.data == 'back_to_groups', state="*")
async def userbots_callback(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    # Завершаем текущее состояние
    await state.finish()

    # Отправляем новое сообщение с выбором типа чатов
    await bot.edit_message_text(
        "Выберите тип чатов:",
        chat_id,
        message_id,
        reply_markup=await chat_types_cb()  # Переход к клавиатуре для выбора типа чатов
    )

async def convert_to_excel(data):
    # Преобразуем в DataFrame
    df = pd.DataFrame(data)

    # Сохраняем в Excel
    df.to_excel("output.xlsx", index=False, engine='openpyxl')
    print("Данные успешно экспортированы в файл output.xlsx")

@dp.callback_query_handler(lambda c: c.data == 'chats_groups')
async def userbots_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    user_chats = await get_user_chats_from_db(chat_id, chat_type="groups")
    supergroup_chats = await get_user_chats_from_db(chat_id, chat_type="supergroups")
    user_chats.extend(supergroup_chats)
    print(user_chats)
    try:
        user_chats = [json.loads(chat) if isinstance(chat, str) else chat for chat in user_chats]
    except json.JSONDecodeError as e:
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=str(chat["title"]) if isinstance(chat["title"], str) else str(chat["title"].get("title", "Без названия")),
                callback_data=f"chat_groups_{chat['id']}"
            )]
            for chat in user_chats
        ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_chats")]]
    )

    await bot.edit_message_text(
        "Выберите чат:", chat_id=chat_id, message_id=message_id, reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith("chat_"))
async def handle_chat_selection(callback_query: types.CallbackQuery):
    try:
        data_parts = callback_query.data.split("_")

        chat_type = data_parts[1]
        chat_id = int(data_parts[2])

        print(f"Chat ID: {chat_id}, Chat Type: {chat_type}")

        user_id = callback_query.from_user.id
        print(f"User ID: {user_id}")

        # Получаем чаты с учетом типа чата
        user_chats = await get_user_chats_from_db(user_id, chat_type=chat_type)
        selected_chat = next((chat for chat in user_chats if chat["id"] == chat_id), None)

        if not selected_chat:
            await bot.answer_callback_query(callback_query.id, text="Чат не найден.")
            return

        # Извлекаем заголовок чата
        chat_title = selected_chat["title"]["title"] if isinstance(selected_chat["title"], dict) else selected_chat["title"]

        # Получаем метки для чата
        marks = await get_marks(admin_id, chat_id, f"{chat_type}_mark")
        marks_text = "Метки отсутствуют." if not marks else "Текущие метки:\n" + "\n".join(f"- {mark}" for mark in marks)

        # Создаем клавиатуру с кнопками для работы с метками
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton(text="✏️ Добавить метку", callback_data=f"add_mark_{chat_type}_{chat_id}"),
            InlineKeyboardButton(text="🗑️ Удалить метку", callback_data=f"remove_mark_{chat_type}_{chat_id}")
        )
        keyboard.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"chats_{chat_type}")
        )

        # Редактируем сообщение с информацией о чате и метках
        await bot.edit_message_text(
            f"Вы выбрали {chat_type} с названием: {chat_title}\n\n{marks_text}",
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
        )

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        await bot.answer_callback_query(callback_query.id, text="Произошла ошибка. Попробуйте снова.")


@dp.callback_query_handler(lambda c: c.data.startswith("add_mark_"))
async def add_mark_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data_parts = callback_query.data.split("_")
    chat_type = data_parts[2]
    chat_id = int(data_parts[3])
    user_id = callback_query.from_user.id


    user_chats = await get_user_chats_from_db(user_id, chat_type=chat_type)
    selected_chat = next((chat for chat in user_chats if chat["id"] == chat_id), None)

    if not selected_chat:
        await bot.answer_callback_query(callback_query.id, text="Чат не найден.")
        return


    chat_title = selected_chat["title"] if isinstance(selected_chat["title"], str) else selected_chat["title"].get(
        "title", "Без названия")


    await bot.answer_callback_query(callback_query.id)
    await state.set_state(MarkState.waiting_for_mark)


    await state.update_data(chat_id=chat_id)

    if chat_type == "channel":
        kb = await chan_back_cb()
    else:
        kb = await grop_back_cb()
    await bot.edit_message_text(
        f"Введите новую метку для {chat_type} с названием: {chat_title}:",
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        reply_markup= kb
    )


@dp.message_handler(state=MarkState.waiting_for_mark)
async def process_new_mark(msg: types.Message, state: FSMContext):
    new_mark = msg.text.strip()
    user_id = msg.from_user.id

    data = await state.get_data()
    chat_id = data.get("chat_id")

    if not chat_id:
        await bot.send_message(user_id, "Произошла ошибка. Чат не найден.")
        return

    if not new_mark:
        await bot.send_message(user_id, "Метка не может быть пустой. Попробуйте снова.")
        return

    existing_marks = await get_marks(admin_id, chat_id, f"groups_mark")

    if new_mark in existing_marks:
        await bot.send_message(user_id, f"Метка '{new_mark}' уже существует для этого чата.")
        return

    await add_mark(admin_id, chat_id, f"groups_mark", new_mark)

    marks = await get_marks(admin_id, chat_id, f"groups_mark")
    marks_text = "Метки отсутствуют." if not marks else "Текущие метки:\n" + "\n".join(f"- {mark}" for mark in marks)

    await state.finish()

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="✏️ Добавить метку", callback_data=f"add_mark_groups_{chat_id}"),
        InlineKeyboardButton(text="🗑️ Удалить метку", callback_data=f"remove_mark_groups_{chat_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"chats_groups")
    )
    await add_column("users", new_mark)
    await bot.send_message(
        user_id,
        f"Метка '{new_mark}' добавлена.\n\n{marks_text}",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith("remove_mark_"))
async def remove_mark_callback(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split("_")
    chat_type = data_parts[2]
    chat_id = int(data_parts[3])
    user_id = callback_query.from_user.id

    marks = await get_marks(admin_id, chat_id, f"{chat_type}_mark")
    if not marks:
        await bot.answer_callback_query(callback_query.id, text="Нет меток для удаления.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=mark, callback_data=f"confirm_remove_mark_{chat_type}_{chat_id}_{mark}")]
            for mark in marks
        ]
    )

    await bot.edit_message_text(
        "Выберите метку для удаления:",
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
    )


@dp.callback_query_handler(lambda c: c.data.startswith("confirm_remove_mark_"))
async def confirm_remove_mark_callback(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split("_")
    chat_type = data_parts[3]
    chat_id = int(data_parts[4])
    mark_to_remove = "_".join(data_parts[5:])
    user_id = callback_query.from_user.id

    await remove_mark(admin_id, f"{chat_type}_mark", {"ch_id": chat_id, "mark": mark_to_remove})


    marks = await get_marks(admin_id, chat_id, f"{chat_type}_mark")
    marks_text = "Метки отсутствуют." if not marks else "Текущие метки:\n" + "\n".join(f"- {mark}" for mark in marks)


    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="✏️ Добавить метку", callback_data=f"add_mark_{chat_type}_{chat_id}"),
        InlineKeyboardButton(text="🗑️ Удалить метку", callback_data=f"remove_mark_{chat_type}_{chat_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"chats_groups")
    )
    try:
        await drop_column("users", mark_to_remove)
    except asyncpg.exceptions.UndefinedColumnError as e:
        print("Error: ", e)
    except ValueError as e:
        print(f"Ошибка ValueError: {e}")
    await bot.edit_message_text(
        f"Вы выбрали группу с ID: {chat_id}\n\nМетка '{mark_to_remove}' удалена.\n\n{marks_text}",
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
    )


@dp.callback_query_handler(lambda c: c.data == 'chats_channels')
async def userbots_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    user_chats = await get_user_chats_from_db(chat_id, chat_type="channels")

    print(f"User chats: {user_chats}")

    try:
        user_chats = [json.loads(chat) if isinstance(chat, str) else chat for chat in user_chats]
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON: {e}")
        return

    if not user_chats:
        print("Каналы не найдены.")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(
                                text=str(chat["title"]) if isinstance(chat["title"], str) else str(
                                    chat["title"].get("title", "Без названия")),
                                callback_data=f"chat_channels_{chat['id']}"
                            )]
                            for chat in user_chats
                        ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_chats")]]
    )

    await bot.edit_message_text(
        "Выберите канал:", chat_id=chat_id, message_id=message_id, reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data.startswith("chat_"))
async def handle_channel_selection(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        data_parts = callback_query.data.split("_")
        chat_type = "channels"
        chat_id = int(data_parts[2])
        print(chat_id)
        user_id = callback_query.from_user.id
        print(user_id)

        user_chats = await get_channels_from_db(user_id)
        selected_chat = next((chat for chat in user_chats if chat["id"] == chat_id), None)

        if not selected_chat:
            await bot.answer_callback_query(callback_query.id, text="Чат не найден.")
            return


        await state.update_data(chat_id=chat_id)

        chat_title = selected_chat["title"]["title"] if isinstance(selected_chat["title"], dict) else selected_chat["title"]

        marks = await get_marks(admin_id, chat_id, f"{chat_type}_mark")

        marks_text = "Метки отсутствуют." if not marks else "Текущие метки:\n" + "\n".join(f"- {mark}" for mark in marks)

        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton(text="✏️ Добавить метку", callback_data=f"add_mark_{chat_type}_{chat_id}"),
            InlineKeyboardButton(text="🗑️ Удалить метку", callback_data=f"remove_mark_{chat_type}_{chat_id}")
        )
        keyboard.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="chats_channels")
        )


        await bot.edit_message_text(
            f"Вы выбрали канал с названием: {chat_title}\n\n{marks_text}",
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
        )

    except Exception as e:
        await bot.answer_callback_query(callback_query.id, text="Произошла ошибка. Попробуйте снова.")



@dp.callback_query_handler(lambda c: c.data.startswith("add_mark_"))
async def add_mark_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data_parts = callback_query.data.split("_")
    chat_type = data_parts[2]
    chat_id = int(data_parts[3])
    user_id = callback_query.from_user.id


    user_chats = await get_user_chats_from_db(user_id, chat_type=chat_type)
    selected_chat = next((chat for chat in user_chats if chat["id"] == chat_id), None)

    if not selected_chat:
        await bot.answer_callback_query(callback_query.id, text="Канал не найден.")
        return


    chat_title = selected_chat["title"] if isinstance(selected_chat["title"], str) else selected_chat["title"].get(
        "title", "Без названия")


    await bot.answer_callback_query(callback_query.id)
    await state.set_state(MarkState.waiting_for_mark)


    await state.update_data(chat_id=chat_id)


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data=f"chat_{chat_type}_{chat_id}")],
        ]
    )


    await bot.edit_message_text(
        f"Введите новую метку для канала с названием: {chat_title}:",
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
    )


@dp.message_handler(state=MarkState.waiting_for_mark)
async def process_new_mark(msg: types.Message, state: FSMContext):
    new_mark = msg.text.strip()
    user_id = msg.from_user.id


    data = await state.get_data()
    chat_id = data.get("chat_id")

    if not chat_id:
        await bot.send_message(user_id, "Произошла ошибка. Канал не найден.")
        return

    if not new_mark:
        await bot.send_message(user_id, "Метка не может быть пустой. Попробуйте снова.")
        return


    existing_marks = await get_marks(admin_id, chat_id, f"channels_mark")


    if new_mark in existing_marks:
        await bot.send_message(user_id, f"Метка '{new_mark}' уже существует для этого канала.")
        return


    await add_mark(admin_id, chat_id, f"channels_mark", new_mark)


    marks = await get_marks(admin_id, chat_id, f"channels_mark")
    marks_text = "Метки отсутствуют." if not marks else "Текущие метки:\n" + "\n".join(f"- {mark}" for mark in marks)


    await state.finish()


    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="✏️ Добавить метку", callback_data=f"add_mark_channels_{chat_id}"),
        InlineKeyboardButton(text="🗑️ Удалить метку", callback_data=f"remove_mark_channels_{chat_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"chats_channels")
    )

    await add_column("users", new_mark)

    await bot.send_message(
        user_id,
        f"Метка '{new_mark}' добавлена.\n\n{marks_text}",
        reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data.startswith("remove_mark_"))
async def remove_mark_callback(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split("_")
    chat_type = data_parts[2]
    chat_id = int(data_parts[3])
    user_id = callback_query.from_user.id


    marks = await get_marks(admin_id, chat_id, f"{chat_type}_mark")
    if not marks:
        await bot.answer_callback_query(callback_query.id, text="Нет меток для удаления.")
        return


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=mark, callback_data=f"confirm_remove_mark_{chat_type}_{chat_id}_{mark}")]
            for mark in marks
        ]
    )

    await bot.edit_message_text(
        "Выберите метку для удаления:",
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
    )


@dp.callback_query_handler(lambda c: c.data.startswith("confirm_remove_mark_"))
async def confirm_remove_mark_callback(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split("_")
    chat_type = data_parts[3]
    chat_id = int(data_parts[4])
    mark_to_remove = "_".join(data_parts[5:])
    user_id = callback_query.from_user.id

    await remove_mark(admin_id, f"{chat_type}_mark", {"ch_id": chat_id, "mark": mark_to_remove})


    marks = await get_marks(admin_id, chat_id, f"{chat_type}_mark")
    marks_text = "Метки отсутствуют." if not marks else "Текущие метки:\n" + "\n".join(f"- {mark}" for mark in marks)


    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="✏️ Добавить метку", callback_data=f"add_mark_{chat_type}_{chat_id}"),
        InlineKeyboardButton(text="🗑️ Удалить метку", callback_data=f"remove_mark_{chat_type}_{chat_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"chats_channels")
    )
    try:
        await drop_column("users", mark_to_remove)
    except asyncpg.exceptions.UndefinedColumnError as e:
        print("Error: ", e)
    except ValueError as e:
        print(f"Ошибка ValueError: {e}")
    await bot.edit_message_text(
        f"Вы выбрали канал с ID: {chat_id}\n\nМетка '{mark_to_remove}' удалена.\n\n{marks_text}",
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
    )

@dp.callback_query_handler(lambda c: c.data == 'stats')
async def userbots_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    groups_stat = await get_stat(admin_id, "groups_stat")
    supergroups_stat = await get_stat(admin_id, "supergroups_stat")
    channels_stat = await get_stat(admin_id, "channels_stat")
    total_stat = groups_stat + supergroups_stat + channels_stat

    status_text = (
        f"📊 Статистика обработки сообщений:\n\n"
        f"👥 Группы: {groups_stat}\n"
        f"👥 Супер-группы: {supergroups_stat}\n"
        f"📢 Каналы: {channels_stat}\n\n"
        f"💬 Всего обработано сообщений: {total_stat}"
    )
    await bot.edit_message_text(status_text, chat_id, message_id, reply_markup=await stats_back_cb())


@dp.callback_query_handler(lambda c: c.data == 'back_to_menu')
async def userbots_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    await bot.edit_message_text("Выберите интересующюю вас функцию:", chat_id, message_id,  reply_markup=await menu_cl())


def main():
    init_db()
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    main()