# Описание / Description
Проект представляет собой набор Telegram-ботов и пользовательских ботов (user-bots) для управления чатами, обработки сообщений и взаимодействия с базой данных. Основные функции включают:  
The project is a set of Telegram bots and user-bots for managing chats, processing messages, and interacting with a database. Key features include:
- Управление чатами (группы, супергруппы, каналы).  
  Chat management (groups, supergroups, channels).
- Добавление, удаление и изменение меток для чатов.  
  Adding, deleting, and modifying chat markers.
- Обработка сообщений с использованием маркеров.  
  Message processing using markers.
- Интеграция с базой данных PostgreSQL.  
  Integration with a PostgreSQL database.

## Структура проекта / Project Structure
- **bot.py**: Основной бот для взаимодействия с пользователями.  
  Main bot for user interaction.
- **pay_bot.py**: Бот для управления платежами и балансом.  
  Bot for managing payments and balances.
- **admin_bot.py**: Бот для администраторов, предоставляющий интерфейс управления.  
  Admin bot providing a management interface.
- **copy/**: Шаблоны и вспомогательные файлы для пользовательских ботов.  
  Templates and helper files for user-bots.
- **database.py**: Модуль для работы с базой данных PostgreSQL.  
  Module for working with the PostgreSQL database.
- **keyboards.py**: Модуль для создания клавиатур Telegram.  
  Module for creating Telegram keyboards.
- **config.py**: Конфигурационный файл с настройками API и базы данных.  
  Configuration file with API and database settings.

## Установка / Installation
1. Убедитесь, что у вас установлен Python 3.8+.  
   Ensure you have Python 3.8+ installed.
2. Установите зависимости:  
   Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Настройте файл `config.py` с вашими данными:  
   Configure the `config.py` file with your data:
   - Telegram API токен.  
     Telegram API token.
   - Данные для подключения к базе данных PostgreSQL.  
     PostgreSQL database connection details.

## Запуск / Running
Для запуска ботов используйте следующие команды:  
Use the following commands to run the bots:

### Админский бот / Admin Bot
```bash
python admin_bot.py
```

### Пользовательский бот / User Bot
```bash
python copy/userbot.py
```

## Основные функции / Key Features
### Управление чатами / Chat Management
- Просмотр доступных чатов (группы, супергруппы, каналы).  
  Viewing available chats (groups, supergroups, channels).
- Добавление, удаление и изменение меток для чатов.  
  Adding, deleting, and modifying chat markers.

### Обработка сообщений / Message Processing
- Автоматическая обработка сообщений на основе заданных маркеров.  
  Automatic message processing based on specified markers.
- Сохранение обработанных сообщений в базу данных.  
  Saving processed messages to the database.

### Администрирование / Administration
- Управление метками и статистикой через админский бот.  
  Managing markers and statistics via the admin bot.

## Логирование / Logging
Логи работы ботов сохраняются в файлы:  
Bot logs are saved to files:
- `userbot.log`
- `bot.log`

## Поддержка / Support
Если у вас возникли вопросы или проблемы, обратитесь в поддержку через бота.  
If you have any questions or issues, contact support via the bot.

## Лицензия / License
Все права защищены © 2025.  
All rights reserved © 2025.
