from config import user, password, host, port, db_name, table_name
import asyncpg
import psycopg2
import asyncio
import json
import re, asyncio
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


async def connect_to_db():
    conn = await asyncpg.connect(
        user=user, password=password, database=db_name, host=host, port=int(port)
    )
    return conn


def init_db():
    """Синхронная версия функции инициализации базы данных"""
    conn = psycopg2.connect(
        user=user, password=password, database=db_name, host=host, port=int(port)
    )
    cursor = conn.cursor()

    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        chat_id BIGINT PRIMARY KEY,
        reg_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        phone_number VARCHAR(15),
        admin_id BIGINT,
        api_id BIGINT,
        api_hash VARCHAR(64),
        bot_token VARCHAR(50),
        bot_password VARCHAR(255),
        email VARCHAR(255),
        balance NUMERIC(15, 2) DEFAULT 0,
        subscription_end_date DATE,
        days_left INTEGER,
        password VARCHAR(255), 
        password_attempts INT DEFAULT 1,
        block_account BOOLEAN DEFAULT FALSE,
        session_chat_task BOOLEAN DEFAULT FALSE,
        ktu_own BOOLEAN DEFAULT FALSE,
        r_user_login BOOLEAN DEFAULT FALSE,
        groups jsonb[],
        supergroups jsonb[],
        channels jsonb[],
        groups_mark jsonb[],
        supergroups_mark jsonb[],
        channels_mark jsonb[],
        groups_msg jsonb[],
        supergroups_msg jsonb[],
        channels_msg jsonb[],
        groups_stat INT DEFAULT 0,
        supergroups_stat INT DEFAULT 0,
        channels_stat INT DEFAULT 0
    );
    """

    cursor.execute(create_table_query)
    conn.commit()
    print("Таблица успешно создана или уже существует.")

    cursor.close()
    conn.close()


async def get_password_attempts(chat_id):
    if not isinstance(chat_id, int) or chat_id <= 0:
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT password_attempts
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            print(f"Количество попыток для пользователя с chat_id {chat_id}: {result}")
            return result
    except Exception as e:
        print(f"Ошибка при получении количества попыток: {e}")
    finally:
        await conn.close()


def is_valid_chat_id(chat_id):
    return isinstance(chat_id, int) and chat_id > 0


async def add_user(chat_id):
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            INSERT INTO {table_name}(chat_id) VALUES($1)
            ON CONFLICT (chat_id) DO NOTHING;
        """,
            chat_id,
        )
        print(f"Пользователь с chat_id {chat_id} добавлен.")
    except Exception as e:
        print(f"Ошибка при добавлении пользователя: {e}")
    finally:
        await conn.close()


async def check_user(chat_id):
    """Проверка, существует ли пользователь в базе данных по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT 1
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result:
            print(f"Пользователь с chat_id {chat_id} найден в базе данных.")
            return True
        else:
            print(f"Пользователь с chat_id {chat_id} не найден в базе данных.")
            return False
    except Exception as e:
        print(f"Ошибка при проверке пользователя: {e}")
        return False
    finally:
        await conn.close()


async def increment_password_attempts(chat_id):
    """Увеличение количества неудачных попыток пароля на 1 для пользователя"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET password_attempts = password_attempts + 1
            WHERE chat_id = $1;
        """,
            chat_id,
        )
        print(
            f"Количество попыток для пользователя с chat_id {chat_id} увеличено на 1."
        )
    except Exception as e:
        print(f"Ошибка при увеличении количества попыток: {e}")
    finally:
        await conn.close()


async def reset_password_attempts(chat_id):
    """Сброс количества неудачных попыток пароля на 0 для пользователя"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET password_attempts = 0
            WHERE chat_id = $1;
        """,
            chat_id,
        )
        print(f"Количество попыток для пользователя с chat_id {chat_id} сброшено на 0.")
    except Exception as e:
        print(f"Ошибка при сбросе количества попыток: {e}")
    finally:
        await conn.close()


async def get_user_block_account_status(chat_id):
    """Получение статуса бана пользователя по chat_id (True или False)"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT block_account
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            return result if result is not None else None
    except Exception as e:
        print(f"Ошибка при получении статуса бана: {e}")
    finally:
        await conn.close()


async def set_user_account_status(chat_id, ban_status):
    """Установка статуса бана для пользователя по chat_id (True или False)"""
    if not isinstance(ban_status, bool):
        raise ValueError("ban_status должен быть типа bool (True или False).")

    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET block_account = $1
            WHERE chat_id = $2;
        """,
            ban_status,
            chat_id,
        )

    except Exception as e:
        print(f"Ошибка при изменении статуса бана: {e}")
    finally:
        await conn.close()


async def get_user_session_chat_task(chat_id):
    """Получение статуса бана пользователя по chat_id (True или False)"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT session_chat_task
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            return result if result is not None else None
    except Exception as e:
        print(f"Ошибка при получении статуса бана: {e}")
    finally:
        await conn.close()

async def set_user_ktu_own(chat_id, ktu_own):
    """Установка статуса бана для пользователя по chat_id (True или False)"""
    if not isinstance(ktu_own, bool):
        raise ValueError("ban_status должен быть типа bool (True или False).")

    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET ktu_own = $1
            WHERE chat_id = $2;
        """,
            ktu_own,
            chat_id,
        )

    except Exception as e:
        print(f"Ошибка при изменении статуса бана: {e}")
    finally:
        await conn.close()


async def get_user_ktu_own(chat_id):
    """Получение статуса бана пользователя по chat_id (True или False)"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT ktu_own
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            return result if result is not None else None
    except Exception as e:
        print(f"Ошибка при получении статуса бана: {e}")
    finally:
        await conn.close()

async def set_user_session_chat_task(chat_id, task_status):
    """Установка статуса бана для пользователя по chat_id (True или False)"""
    if not isinstance(task_status, bool):
        raise ValueError("ban_status должен быть типа bool (True или False).")

    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET session_chat_task = $1
            WHERE chat_id = $2;
        """,
            task_status,
            chat_id,
        )

    except Exception as e:
        print(f"Ошибка при изменении статуса бана: {e}")
    finally:
        await conn.close()


async def jsonb_contains(chat_id, column_name, value):
    """Проверяет, существует ли значение в JSONB ячейке."""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    value = str(value)

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT $1 IN (SELECT jsonb_array_elements_text({column_name}) FROM {table_name} WHERE chat_id = $2)
        """,
            value,
            chat_id,
        )

        if result:
            print(
                f"Значение {value} уже существует в {column_name} для chat_id {chat_id}."
            )
            return True
        else:
            print(
                f"Значение {value} отсутствует в {column_name} для chat_id {chat_id}."
            )
            return False
    except Exception as e:
        print(f"Ошибка при проверке значения в {column_name}: {e}")
        return False
    finally:
        await conn.close()


async def add_ch_info(chat_id, ch_id, ch_title, ch_type, ch_name):
    conn = await connect_to_db()

    group_info = {"ch_id": ch_id, ch_name: ch_title}
    json_str = json.dumps(group_info)
    await conn.execute(
        f"""
        UPDATE {table_name}
        SET {ch_type} = array_append({ch_type}, $1::JSONB)
        WHERE chat_id = $2;
    """,
        json_str,
        chat_id,
    )
    await conn.close()


async def check_group(chat_id, ch_id_to_check, ch_str: str):
    conn = await connect_to_db()

    groups_data = await conn.fetchval(
        f"""
        SELECT {ch_str}
        FROM {table_name}
        WHERE chat_id = $1;
    """,
        chat_id,
    )

    await conn.close()

    if not groups_data:
        return False

    groups = [json.loads(group) for group in groups_data]

    for group in groups:
        if group.get("ch_id") == ch_id_to_check:
            return True

    return False


async def check_msg(chat_id, text_to_search, ch_str: str):
    conn = await connect_to_db()

    groups_data = await conn.fetchval(
        f"""
        SELECT {ch_str}
        FROM {table_name}
        WHERE chat_id = $1;
    """,
        chat_id,
    )

    await conn.close()

    if not groups_data:
        return False

    messages = [json.loads(group) for group in groups_data]

    for message in messages:
        if text_to_search in message.get("text", ""):
            return True

    return False

async def get_user_email(chat_id):
    """Получение email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT email
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            print(f"Email пользователя с chat_id {chat_id}: {result}")
            return result
    except Exception as e:
        print(f"Ошибка при получении email: {e}")
    finally:
        await conn.close()

async def update_user_email(chat_id, new_email):
    """Обновление email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    if not validate_email(new_email):
        raise ValueError("Неверный формат email.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET email = $1
            WHERE chat_id = $2;
        """,
            new_email,
            chat_id,
        )
        print(f"Email для пользователя с chat_id {chat_id} обновлен на {new_email}.")
    except Exception as e:
        print(f"Ошибка при обновлении email: {e}")
    finally:
        await conn.close()

async def get_user_password(chat_id):
    """Получение пароля пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT password
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            print(f"Пароль для пользователя с chat_id {chat_id}: {result}")
            return result
    except Exception as e:
        print(f"Ошибка при получении пароля: {e}")
    finally:
        await conn.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def validate_email(email: str) -> bool:
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(email_regex, email) is not None

def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    return True

async def update_user_password(chat_id, new_password):
    """Обновление пароля пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    if not validate_password(new_password):
        raise ValueError("Пароль должен содержать минимум 8 символов, включая строчные и прописные буквы и цифры.")

    hashed_password = hash_password(new_password)

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET password = $1
            WHERE chat_id = $2;
        """,
            hashed_password,
            chat_id,
        )
    except Exception as e:
        print(f"Ошибка при обновлении пароля: {e}")
    finally:
        await conn.close()

async def check_email_exists(chat_id):
    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT email 
            FROM {table_name} 
            WHERE chat_id = $1;
            """,
            chat_id,
        )
        return result is not None
    except Exception as e:
        print(f"Ошибка при проверке email: {e}")
    finally:
        await conn.close()

async def save_email_to_db(chat_id, email):
    """Сохранение email в базе данных для конкретного chat_id"""
    conn = await connect_to_db()
    email = email
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET email = $1
            WHERE chat_id = $2;
            """,
            email,
            chat_id,
        )
    except Exception as e:
        print(f"Ошибка при сохранении email: {e}")
    finally:
        await conn.close()

async def get_user_balance(chat_id):
    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT balance 
            FROM {table_name} 
            WHERE chat_id = $1;
            """,
            chat_id,
        )
        return result
    except Exception as e:
        print(f"Ошибка при проверке balance: {e}")
    finally:
        await conn.close()

async def update_user_balance(chat_id, new_balance):
    conn = await connect_to_db()
    try:
        # Обновление значения balance
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET balance = $1
            WHERE chat_id = $2;
            """,
            new_balance,  # новый баланс
            chat_id,      # chat_id пользователя
        )
        print(f"Баланс для chat_id {chat_id} обновлен на {new_balance}.")
    except Exception as e:
        print(f"Ошибка при обновлении баланса: {e}")
    finally:
        await conn.close()

async def get_user_api_id(chat_id):
    """Получение email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT api_id
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            print(f"api_id пользователя с chat_id {chat_id}: {result}")
            return result
    except Exception as e:
        print(f"Ошибка при получении api_id: {e}")
    finally:
        await conn.close()

async def update_user_api_id(chat_id, api_id):
    """Обновление email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET api_id = $1
            WHERE chat_id = $2;
        """,
            api_id,
            chat_id,
        )
        print(f"api_id для пользователя с chat_id {chat_id} обновлен на {api_id}.")
    except Exception as e:
        print(f"Ошибка при обновлении email: {e}")
    finally:
        await conn.close()

async def get_user_admin_id(chat_id):
    """Получение email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT admin_id
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            print(f"admin_id пользователя с chat_id {chat_id}: {result}")
            return result
    except Exception as e:
        print(f"Ошибка при получении api_id: {e}")
    finally:
        await conn.close()

async def update_user_admin_id(chat_id, admin_id):
    """Обновление email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET admin_id = $1
            WHERE chat_id = $2;
        """,
            admin_id,
            chat_id,
        )
        print(f"admin_id для пользователя с chat_id {chat_id} обновлен на {admin_id}.")
    except Exception as e:
        print(f"Ошибка при обновлении email: {e}")
    finally:
        await conn.close()

async def get_user_api_hash(chat_id):
    """Получение email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT api_hash
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            print(f"api_hash пользователя с chat_id {chat_id}: {result}")
            return result
    except Exception as e:
        print(f"Ошибка при получении api_hash: {e}")
    finally:
        await conn.close()

async def update_user_api_hash(chat_id, api_hash):
    """Обновление email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET api_hash = $1
            WHERE chat_id = $2;
        """,
            api_hash,
            chat_id,
        )
        print(f"api_hash для пользователя с chat_id {chat_id} обновлен на {api_hash}.")
    except Exception as e:
        print(f"Ошибка при обновлении api_hash: {e}")
    finally:
        await conn.close()

async def get_user_bot_token(chat_id):
    """Получение email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT bot_token
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            print(f"bot_token пользователя с chat_id {chat_id}: {result}")
            return result
    except Exception as e:
        print(f"Ошибка при получении bot_token: {e}")
    finally:
        await conn.close()

async def update_user_bot_token(chat_id, bot_token):
    """Обновление email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")


    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET bot_token = $1
            WHERE chat_id = $2;
        """,
            bot_token,
            chat_id,
        )
        print(f"bot_token для пользователя с chat_id {chat_id} обновлен на {bot_token}.")
    except Exception as e:
        print(f"Ошибка при обновлении api_hash: {e}")
    finally:
        await conn.close()

async def get_user_phone_number(chat_id):
    """Получение email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT phone_number
            FROM {table_name}
            WHERE chat_id = $1;
        """,
            chat_id,
        )

        if result is None:
            print(f"Пользователь с chat_id {chat_id} не найден.")
            return None
        else:
            print(f"phone_number пользователя с chat_id {chat_id}: {result}")
            return result
    except Exception as e:
        print(f"Ошибка при получении bot_token: {e}")
    finally:
        await conn.close()

async def update_user_phone_number(chat_id, phone_number):
    """Обновление email пользователя по chat_id"""
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET phone_number = $1
            WHERE chat_id = $2;
        """,
            phone_number,
            chat_id,
        )
        print(f"phone_number для пользователя с chat_id {chat_id} обновлен на {phone_number}.")
    except Exception as e:
        print(f"Ошибка при обновлении phone_number: {e}")
    finally:
        await conn.close()


async def find_chat_id_by_email(email: str):
    # Подключение к базе данных
    conn = await connect_to_db()

    # SQL-запрос для поиска chat_id по email
    query = """
        SELECT chat_id
        FROM users
        WHERE email = $1;
    """

    # Выполнение запроса с передачей email
    result = await conn.fetch(query, email)

    # Проверяем, если результат не пустой
    if result:
        print(f"Chat ID для email {email}: {result[0]['chat_id']}")
        return result[0]['chat_id']
    else:
        print(f"Пользователь с email {email} не найден.")

    # Закрываем соединение
    await conn.close()

async def get_marks(chat_id, ch_id, column_name):
    """
    Получает метки для указанного чата из базы данных.
    """
    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT {column_name}
            FROM {table_name}
            WHERE chat_id = $1;
            """,
            chat_id,
        )

        if result:
            # Преобразуем строки JSON в словари
            marks_list = [json.loads(mark) for mark in result]

            # Фильтруем метки по ch_id
            marks = [mark["mark"] for mark in marks_list if mark.get("ch_id") == ch_id]
            return marks
        return []
    except Exception as e:
        return []
    finally:
        await conn.close()

async def increment_stat(chat_id, stat_type):
    """
    Увеличивает значение статистики на 1.
    :param chat_id: ID чата.
    :param stat_type: Тип статистики (например, "groups_stat").
    """
    if stat_type not in ["groups_stat", "supergroups_stat", "channels_stat"]:
        raise ValueError("Недопустимый тип статистики.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET {stat_type} = {stat_type} + 1
            WHERE chat_id = $1;
            """,
            chat_id,
        )
        print(f"Статистика {stat_type} увеличена на 1 для chat_id {chat_id}.")
    except Exception as e:
        print(f"Ошибка при увеличении статистики {stat_type}: {e}")
    finally:
        await conn.close()


async def initialize_jsonb_column(chat_id, column_name):
    """
    Инициализирует колонку JSONB как пустой массив, если она NULL.
    """
    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET {column_name} = ARRAY[]::JSONB[]
            WHERE chat_id = $1 AND {column_name} IS NULL;
        """,
            chat_id,
        )
        print(f"Колонка {column_name} инициализирована как пустой массив для chat_id {chat_id}.")
    except Exception as e:
        print(f"Ошибка при инициализации колонки {column_name}: {e}")
    finally:
        await conn.close()

async def add_mark(chat_id, ch_id, column_name, mark_title):
    """
    Добавляет метку в указанный столбец JSONB для заданного chat_id.

    :param chat_id: ID чата, для которого нужно добавить метку.
    :param ch_id: ID группы.
    :param column_name: Название столбца, куда добавляется метка.
    :param mark_title: Название метки.
    """
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    mark = {"ch_id": ch_id, "mark": mark_title}
    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET {column_name} = array_append({column_name}, $1::JSONB)
            WHERE chat_id = $2;
        """,
            json.dumps(mark),
            chat_id,
        )
        print(f"Метка добавлена в {column_name} для chat_id {chat_id}: {mark}")
    except Exception as e:
        print(f"Ошибка при добавлении метки: {e}")
    finally:
        await conn.close()


async def remove_mark(chat_id, column_name, mark):
    """
    Удаляет метку из указанного столбца JSONB для заданного chat_id.

    :param chat_id: ID чата, для которого нужно удалить метку.
    :param column_name: Название столбца, откуда удаляется метка.
    :param mark: Метка для удаления.
    """
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET {column_name} = array_remove({column_name}, $1::JSONB)
            WHERE chat_id = $2;
        """,
            json.dumps(mark),
            chat_id,
        )
        print(f"Метка удалена из {column_name} для chat_id {chat_id}.")
    except Exception as e:
        print(f"Ошибка при удалении метки: {e}")
    finally:
        await conn.close()


async def update_mark(chat_id, column_name, old_mark, new_mark):
    """
    Обновляет метку в указанном столбце JSONB для заданного chat_id.

    :param chat_id: ID чата, для которого нужно обновить метку.
    :param column_name: Название столбца, где обновляется метка.
    :param old_mark: Старая метка для замены.
    :param new_mark: Новая метка для замены.
    """
    if not is_valid_chat_id(chat_id):
        raise ValueError("Неверный chat_id. Он должен быть положительным целым числом.")

    conn = await connect_to_db()
    try:
        # Удаляем старую метку
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET {column_name} = array_remove({column_name}, $1::JSONB)
            WHERE chat_id = $2;
        """,
            json.dumps(old_mark),
            chat_id,
        )
        # Добавляем новую метку
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET {column_name} = array_append({column_name}, $1::JSONB)
            WHERE chat_id = $2;
        """,
            json.dumps(new_mark),
            chat_id,
        )
        print(f"Метка обновлена в {column_name} для chat_id {chat_id}.")
    except Exception as e:
        print(f"Ошибка при обновлении метки: {e}")
    finally:
        await conn.close()


async def get_user_chats_from_db(chat_id, chat_type=None):
    """
    Получает список чатов пользователя из базы данных.
    :param chat_id: ID пользователя
    :param chat_type: Тип чатов ("groups", "supergroups", "channels")
    """
    conn = await connect_to_db()
    try:
        if (chat_type == "groups"):
            query = f"SELECT jsonb_array_elements(array_to_json(groups)::jsonb) AS chat FROM {table_name} WHERE chat_id = $1"
        elif (chat_type == "supergroups"):
            query = f"SELECT jsonb_array_elements(array_to_json(supergroups)::jsonb) AS chat FROM {table_name} WHERE chat_id = $1"
        elif (chat_type == "channels"):
            query = f"SELECT jsonb_array_elements(array_to_json(channels)::jsonb) AS chat FROM {table_name} WHERE chat_id = $1"
        else:
            raise ValueError("Неверный тип чатов. Допустимые значения: 'groups', 'supergroups', 'channels'.")

        result = await conn.fetch(query, chat_id)

        # Преобразуем результат в список словарей
        chats = []
        for record in result:
            chat_data = json.loads(record["chat"])  # Преобразуем строку JSON в объект Python
            chats.append({"id": chat_data["ch_id"], "title": chat_data["title"]})

        return chats
    except Exception as e:
        print(f"Ошибка при получении чатов из базы данных: {e}")
        return []
    finally:
        await conn.close()

async def get_stat(chat_id, stat_type):
    """
    Получает статистику по указанному типу.
    :param chat_id: ID чата.
    :param stat_type: Тип статистики (например, "groups_stat").
    :return: Значение статистики.
    """
    if stat_type not in ["groups_stat", "supergroups_stat", "channels_stat"]:
        raise ValueError("Недопустимый тип статистики.")

    conn = await connect_to_db()
    try:
        result = await conn.fetchval(
            f"""
            SELECT {stat_type}
            FROM {table_name}
            WHERE chat_id = $1;
            """,
            chat_id,
        )
        return result if result is not None else 0
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return 0
    finally:
        await conn.close()





