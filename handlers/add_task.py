# app/routers/add_task.py
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.tasks import categories_kb, confirm_kb
from models.db import get_sessionmaker
from states.add_task import AddTaskStates
from storage.repo import ensure_user, get_or_create_category
from utils.datetime_parse import parse_deadline

router = Router()

DEFAULT_CATS = ["Аналитика", "Разработка", "Дизайн", "Тестирование", "Другое"]


@router.message(F.text == "➕ Добавить задачу")
async def add_entry(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddTaskStates.choosing_category)
    await message.answer(
        "Выберите категорию:", reply_markup=categories_kb(DEFAULT_CATS)
    )


@router.callback_query(AddTaskStates.choosing_category, F.data.startswith("cat:"))
async def pick_category(cb: CallbackQuery, state: FSMContext):
    raw = cb.data.split(":", 1)[1]
    cat_name = None if raw == "__none__" else raw
    await state.update_data(category=cat_name)
    await state.set_state(AddTaskStates.typing_title)
    await cb.message.edit_text("Введите название задачи (кратко, до 200 символов):")
    await cb.answer()


@router.message(AddTaskStates.typing_title, F.text)
async def type_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if not title or len(title) > 200:
        await message.answer("Пожалуйста, введите непустое название (≤ 200 символов).")
        return
    await state.update_data(title=title)
    await state.set_state(AddTaskStates.typing_deadline)
    await message.answer(
        "Введите дедлайн в формате YYYY-MM-DD или YYYY-MM-DD HH:MM.\n"
        "Или напишите «без дедлайна»."
    )


@router.message(AddTaskStates.typing_deadline, F.text)
async def type_deadline(message: Message, state: FSMContext):
    try:
        deadline = parse_deadline(message.text)
    except ValueError as e:
        await message.answer(str(e))
        return
    await state.update_data(deadline=deadline.isoformat() if deadline else None)
    data = await state.get_data()
    cat = data.get("category") or "—"
    ttl = data.get("title")
    dl = deadline.strftime("%Y-%m-%d %H:%M") if deadline else "нет"
    await state.set_state(AddTaskStates.confirm)
    await message.answer(
        f"<b>Проверьте:</b>\nКатегория: <code>{cat}</code>\nЗадача: <code>{ttl}</code>\nДедлайн: <code>{dl}</code>",
        parse_mode="HTML",
        reply_markup=confirm_kb(),
    )


@router.callback_query(AddTaskStates.confirm, F.data == "task:cancel")
async def cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Отменено.")
    await cb.answer()


@router.callback_query(AddTaskStates.confirm, F.data == "task:save")
async def save(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat_name = data.get("category")
    title = data.get("title")
    deadline_iso = data.get("deadline")

    Session = get_sessionmaker()
    async with Session() as session:
        await ensure_user(session, cb.from_user.id, cb.from_user.username)
        category = None
        if cat_name:
            category = await get_or_create_category(
                session, user_id=None, name=cat_name
            )  # системная категория
        from datetime import datetime

        from storage.repo import create_task

        dl = datetime.fromisoformat(deadline_iso) if deadline_iso else None
        await create_task(session, cb.from_user.id, title, category, dl)
        await session.commit()

    await state.clear()
    await cb.message.edit_text("✅ Задача сохранена!")
    await cb.answer()
