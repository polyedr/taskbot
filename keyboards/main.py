# app/keyboards/main.py
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="📋 Список дел"), KeyboardButton(text="✅ Выполненные")],
        [KeyboardButton(text="✉️ Обратная связь")],
    ],
    resize_keyboard=True,
)

START_TEXT = (
    "Привет! Я трекер задач. Добавляй задачи, ставь дедлайны и отмечай готовность."
)
