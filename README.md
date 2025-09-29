# Task Tracker Bot

Telegram-бот для ведения личных задач. Написан на **Python 3.12**, использует
**Aiogram 3**, **SQLAlchemy (async)** и **PostgreSQL**.

## Возможности

- ➕ Добавление задач
  - выбор категории (Аналитика, Разработка, Дизайн и др.)
  - ввод названия
  - ввод дедлайна (формат `YYYY-MM-DD` или `YYYY-MM-DD HH:MM`, поддерживаются «сегодня», «завтра»)
- 📋 Просмотр списка активных задач
  - сортировка по ближайшему дедлайну
  - отметка задачи как выполненной
- ✅ Просмотр истории выполненных задач
- ✉️ Отправка обратной связи администраторам

## Стек

- Python 3.12
- [Aiogram 3](https://docs.aiogram.dev/)
- [SQLAlchemy 2](https://docs.sqlalchemy.org/)
- PostgreSQL
- python-dotenv

## Установка

```bash
git clone <repo_url>
cd taskbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Конфигурация

Создайте файл `.env` в корне проекта по образцу:

```
cp .env.example .env
```

- `BOT_TOKEN` — токен, выданный BotFather
- `PG_DSN` — строка подключения к PostgreSQL (с драйвером asyncpg)
- `ADMINS` — список ID администраторов (через запятую), будут получать обратную связь

## Запуск

```bash
python bot.py
```

При первом запуске создаются таблицы в базе.

## Структура проекта

```
bot.py                # точка входа
config.py             # конфиг, чтение .env
db.py                 # engine и init_db
models/
    task.py           # модели User, Category, Task
    feedback.py       # модель Feedback
handlers/
    start.py          # /start
    add_task.py       # FSM добавления задачи
    tasks.py          # список/история/выполнение
    feedback.py       # обратная связь
keyboards/
    menu.py           # главное меню
    tasks.py          # инлайн-кнопки для задач
services/
    datetime_parse.py # парсинг дат
middlewares/
    anti_spam.py      # антиспам
```

## Полезные команды

- `/start` — запуск бота, главное меню
- «➕ Добавить задачу» — мастер добавления
- «📋 Список дел» — текущие активные задачи
- «✅ Выполненные» — последние 10 закрытых задач
- «✉️ Обратная связь» — сообщение администраторам

---

© 2025 Task Tracker Bot
