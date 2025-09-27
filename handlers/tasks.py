# app/routers/tasks.py
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from keyboards.tasks import tasks_list_kb
from models.db import get_sessionmaker
from models.task import Task
from storage.repo import (
    count_tasks_active,
    list_tasks_active,
    list_tasks_done,
    mark_done,
)

router = Router()
PAGE_SIZE = 5


def _render_task_line(t) -> str:
    cat = f"[{t.category.name}] " if t.category else ""
    dl = f" — до {t.deadline_ts:%Y-%m-%d %H:%M}" if t.deadline_ts else ""
    return f"[#{t.id}] {cat}{t.title}{dl}"


@router.message(F.text == "📋 Список дел")
async def show_active(message: Message):
    await _send_active_page(message.chat.id, message, page=0)


async def _send_active_page(chat_id: int, message_or_cb, page: int):
    Session = get_sessionmaker()
    async with Session() as session:
        tasks, total = await _list_active(chat_id, PAGE_SIZE, page * PAGE_SIZE)
    has_next = (page + 1) * PAGE_SIZE < total
    lines = "\n".join(_render_task_line(t) for t in tasks) or "Активных задач нет."
    pairs = [(t.id, t.title) for t in tasks]
    kb = tasks_list_kb(pairs, page=page, has_next=has_next, done_buttons=True)
    await message_or_cb.answer(
        f"<b>Активные задачи</b>:\n{lines}", parse_mode="HTML", reply_markup=kb
    )


@router.callback_query(F.data.startswith("page:"))
async def paginate(cb: CallbackQuery):
    page = int(cb.data.split(":")[1])
    await cb.message.delete()
    await _send_active_page(cb.from_user.id, cb.message, page=page)
    await cb.answer()


@router.callback_query(F.data.startswith("taskdone:"))
async def done(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[1])
    Session = get_sessionmaker()
    async with Session() as session:
        ok = await mark_done(session, task_id, cb.from_user.id)
        if ok:
            await session.commit()
    await cb.answer(
        "Готово!" if ok else "Не удалось (возможно, уже завершена).", show_alert=False
    )
    await cb.message.delete()
    # показать первую страницу заново
    await _send_active_page(cb.from_user.id, cb.message, page=0)


async def _list_active(uid: int, limit: int, offset: int):
    Session = get_sessionmaker()
    async with Session() as session:
        q = (
            select(Task)
            .options(selectinload(Task.category))  # << вот это
            .where(Task.user_id == uid, Task.is_done.is_(False))
            .order_by(Task.deadline_ts.is_(None), Task.deadline_ts, Task.created_ts)
            .limit(limit)
            .offset(offset)
        )
        res = await session.execute(q)
        tasks = list(res.scalars().all())

        q2 = select(Task).where(Task.user_id == uid, Task.is_done.is_(False))
        res2 = await session.execute(q2)
        total = len(res2.scalars().all())
    return tasks, total


@router.message(F.text == "✅ Выполненные")
async def show_done(message: Message):
    Session = get_sessionmaker()
    async with Session() as session:
        q = (
            select(Task)
            .options(selectinload(Task.category))  # << и тут
            .where(Task.user_id == message.from_user.id, Task.is_done.is_(True))
            .order_by(Task.done_ts.desc())
            .limit(10)
        )
        res = await session.execute(q)
        tasks = list(res.scalars().all())
    if not tasks:
        await message.answer("История выполненных задач пуста.")
        return
    lines = "\n".join(
        f"[#{t.id}] {t.title} — {t.done_ts:%Y-%m-%d %H:%M}" for t in tasks
    )
    await message.answer(
        f"<b>Выполненные (последние 10)</b>:\n{lines}", parse_mode="HTML"
    )
