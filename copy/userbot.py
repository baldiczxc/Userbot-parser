"""Пример простого User-Бот для Telegram"""
import time
import logging
from pyrogram import Client, filters, idle
from config import *
import g4f, asyncio
from database import *

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("./userbot.log", mode="w")],
)
logger = logging.getLogger(__name__)

usb = Client("userbot", api_id=api_id, api_hash=api_hash, phone_number=phone_number)
allowed_chat_types = ["ChatType.GROUP", "ChatType.SUPERGROUP", "ChatType.CHANNEL"]
start_time = time.time()


@usb.on_message(filters.command("ping", prefixes="//"))
async def ping(client, msg):
    """Ping function"""
    logger.info(
        "Получена команда //ping от пользователя %d (%s)",
        msg.from_user.id,
        msg.from_user.username,
    )

    if await check_for_admin(msg.from_user.id):
        await msg.delete()

        bot_info = await client.get_me()
        bot_username = bot_info.username
        bot_id = bot_info.id

        sent_time = time.time()
        sent_message = await msg.reply_text("🚀Pong!🏓")
        received_time = time.time()
        ping_time = (received_time - sent_time) * 1000

        await sent_message.edit_text(
            f"🚀Pong! 🏓\n"
            f"🤖 Юзер-Бот аккаунта: @{bot_username} (ID: {bot_id})\n"
            f"⚡Скорость отклика Telegram: {ping_time:.2f} мс\n"
            f"⏱ Время с момента запуска бота: {await custom_format_time(time.time() - start_time)}"
        )

        logger.info(
            "Ответ на команду //ping отправлен пользователю %d", msg.from_user.id
        )
    else:
        await msg.delete()
        await msg.reply_text("У вас нет разрешения на выполнение команды //ping.")
        logger.warning(
            "%d (%s) пытался выполнить команду //ping.",
            msg.from_user.id,
            msg.from_user.username,
        )


async def check_for_admin(chat_id):
    """Checking administrator rights"""
    return chat_id == admin_id


async def custom_format_time(seconds):
    """A block for managing the date and time format"""
    days = int(seconds // (24 * 3600))
    hours = int((seconds % (24 * 3600)) // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    formatted_time = f"{days}д {hours}ч {minutes}м {seconds}с"
    return formatted_time


async def get_all_chats():
    async for chat in usb.get_dialogs():
        ch_type = str(chat.chat.type)
        ch_id = chat.chat.id
        ch_title = chat.chat.title
        if ch_type in allowed_chat_types:
            group_info = {"ch_id": ch_id, "title": ch_title}
            if ch_type == "ChatType.GROUP":
                check_ch = await check_group(admin_id, ch_id, "groups")
                if not check_ch:
                    await add_ch_info(admin_id, ch_id, group_info, "groups", "title")
                print(group_info)
            elif ch_type == "ChatType.SUPERGROUP":
                check_ch = await check_group(admin_id, ch_id, "supergroups")
                if not check_ch:
                    await add_ch_info(admin_id, ch_id, group_info, "supergroups", "title")
                print(group_info)
            elif ch_type == "ChatType.CHANNEL":
                check_ch = await check_group(admin_id, ch_id, "channels")
                if not check_ch:
                    await add_ch_info(admin_id, ch_id, group_info, "channels", "title")
                print(group_info)


@usb.on_message(filters.command("grab_msg", prefixes="//"))
async def fetch_full_history(client, message):
    print("Начинаем обработку всех чатов...")

    try:
        async for dialog in usb.get_dialogs():
            ch_id = dialog.chat.id
            ch_title = dialog.chat.title
            ch_type = str(dialog.chat.type)

            print(f"Обрабатываем чат: {ch_title} (ID: {ch_id}, Тип: {ch_type})")


            if ch_type == "ChatType.GROUP":
                ch_type_db = "groups_msg"
                markers_column = "groups_mark"
            elif ch_type == "ChatType.SUPERGROUP":
                ch_type_db = "supergroups_msg"
                markers_column = "supergroups_mark"
            elif ch_type == "ChatType.CHANNEL":
                ch_type_db = "channels_msg"
                markers_column = "channels_mark"
            else:
                print(f"Тип чата {ch_type} не поддерживается.")
                continue

            print(f"Используемая таблица: {ch_type_db}")


            markers = await get_marks(admin_id, ch_id, markers_column)
            if not markers:
                print(f"Маркеры не найдены для чата {ch_title}. Пропускаем.")
                continue


            await initialize_jsonb_column(admin_id, ch_type_db)

            total_msg = 0

            try:
                async for msg in usb.get_chat_history(ch_id):
                    total_msg += 1
                    if not msg.text:
                        continue

                    check_ms = await check_msg(admin_id, msg.text, ch_type_db)
                    if not check_ms:
                        for word in markers:
                            if word in msg.text:
                                processed_text = await send_processing(msg.text)
                                print(f"Добавляем обработанное сообщение в {ch_type_db}: {processed_text}")
                                await add_ch_info(
                                    admin_id,
                                    ch_id,
                                    processed_text,
                                    ch_type_db,
                                    "text",
                                )
                    await asyncio.sleep(0.5)
                print(f"Всего обработано сообщений в чате {ch_title}: {total_msg}")
            except Exception as e:
                print(f"Произошла ошибка при обработке чата {ch_title}: {e}")
                continue

    except Exception as e:
        print(f"Произошла ошибка при обработке всех чатов: {e}")
        await message.reply(f"Произошла ошибка: {e}")


async def send_processing(text):
    def send_response():
        test = """
Название: {НАЗВАНИЕ ВАКАНСИИ}
ЗП: {СУММА}
Требование: {ТРЕБОВАНИЯ ИЗ ОБЬЯВЛЕНИЯ ЕСЛИ ЕСТЬ ИНАЧЕ None}
График: {ГРАФИК}
Удаленка: {True/False}
"""
        result = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4o,
            messages=[
                {
                    "role": "user",
                    "content": f"Собери данные СТРОГО! НЕ ДОБОВЛЯЯ НЕЧЕГО БОЛЕЕ! В ОТВЕТЕ ДАЙ ТОЛЬКО ГОТОВЫЙ ОТВЕТ. на примере {test} из этого сообщения:\n\n"
                    + text,
                }
            ],
            web_search=False,
        )
        if isinstance(result, list):
            result = "".join([str(chunk) for chunk in result])
        return result

    response = await asyncio.to_thread(send_response)
    return response


async def process_all_chats():
    """Функция для автоматической обработки всех чатов при старте бота."""
    print("Начинаем автоматическую обработку всех чатов...")

    try:
        async for dialog in usb.get_dialogs():
            ch_id = dialog.chat.id
            ch_title = dialog.chat.title
            ch_type = str(dialog.chat.type)

            print(f"Обрабатываем чат: {ch_title} (ID: {ch_id}, Тип: {ch_type})")


            if (ch_type == "ChatType.GROUP"):
                ch_type_db = "groups_msg"
                markers_column = "groups_mark"
            elif (ch_type == "ChatType.SUPERGROUP"):
                ch_type_db = "supergroups_msg"
                markers_column = "supergroups_mark"
            elif (ch_type == "ChatType.CHANNEL"):
                ch_type_db = "channels_msg"
                markers_column = "channels_mark"
            else:
                print(f"Тип чата {ch_type} не поддерживается.")
                continue


            markers = await get_marks(admin_id, ch_id, markers_column)
            if not markers:
                print(f"Маркеры не найдены для чата {ch_title}. Пропускаем.")
                continue


            await initialize_jsonb_column(admin_id, ch_type_db)

            total_msg = 0

            try:
                async for msg in usb.get_chat_history(ch_id):
                    total_msg += 1
                    if not msg.text:
                        continue

                    check_ms = await check_msg(admin_id, msg.text, ch_type_db)
                    if not check_ms:
                        for word in markers:
                            if word in msg.text:
                                processed_text = await send_processing(msg.text)
                                print(f"Добавляем обработанное сообщение в {ch_type_db}: {processed_text}")
                                await add_ch_info(
                                    admin_id,
                                    ch_id,
                                    processed_text,
                                    ch_type_db,
                                    "text",
                                )
                    await asyncio.sleep(0.5)
                print(f"Всего обработано сообщений в чате {ch_title}: {total_msg}")
            except Exception as e:
                print(f"Произошла ошибка при обработке чата {ch_title}: {e}")
                continue

        print("Обработка всех чатов завершена.")

    except Exception as e:
        print(f"Произошла ошибка при обработке всех чатов: {e}")


@usb.on_message(filters.text)
async def handle_new_message(client, message):
    session_chat_task = await get_user_session_chat_task(admin_id)
    if not session_chat_task:
        await fetch_full_history(client, message)
        await get_all_chats()
        await set_user_session_chat_task(admin_id, True)
        await process_all_chats()

    chat_type = str(message.chat.type)
    if chat_type in allowed_chat_types:
        if chat_type == "ChatType.GROUP":
            text = message.text
            generate = await send_processing(text)
            print(f"{generate}")
            await increment_stat(admin_id, "groups_stat")
        elif chat_type == "ChatType.SUPERGROUP":
            text = message.text
            generate = await send_processing(text)
            print(f"{generate}")
            await increment_stat(admin_id, "supergroups_stat")
        elif chat_type == "ChatType.CHANNEL":
            text = message.text
            generate = await send_processing(text)
            print(f"{generate}")
            await increment_stat(admin_id, "channels_stat")

        await message.reply(f"Сообщение в чате типа: {chat_type}")


if __name__ == "__main__":
    logger.info("Бот запущен.")
    init_db()

    async def on_start():
        await set_user_session_chat_task(admin_id, False)

    async def start_bot():
        await usb.start()
        await on_start()
        logger.info("Клиент успешно запущен.")
        await idle()

    usb.run(start_bot())
