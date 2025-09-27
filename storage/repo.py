# app/storage/repo.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Category, Task, User


# Пользователь
async def ensure_user(session: AsyncSession, user_id: int, username: str | None):
    user = await session.get(User, user_id)
    if not user:
        user = User(user_id=user_id, username=username)
        session.add(user)
        await session.flush()
    return user


# Категории
async def get_or_create_category(
    session: AsyncSession, user_id: int | None, name: str
) -> Category:
    q = select(Category).where(Category.user_id == user_id, Category.name == name)
    res = await session.execute(q)
    cat = res.scalar_one_or_none()
    if not cat:
        cat = Category(name=name, user_id=user_id)
        session.add(cat)
        await session.flush()
    return cat


async def list_categories(session: AsyncSession, user_id: int | None):
    q = select(Category).where(Category.user_id == user_id)
    res = await session.execute(q)
    return list(res.scalars().all())


# Задачи
async def create_task(
    session: AsyncSession,
    user_id: int,
    title: str,
    category: Category | None,
    deadline: datetime | None,
):
    task = Task(user_id=user_id, title=title, category=category, deadline_ts=deadline)
    session.add(task)
    await session.flush()
    return task


async def list_tasks_active(
    session: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
):
    q = (
        select(Task)
        .where(Task.user_id == user_id, Task.is_done.is_(False))
        .order_by(Task.deadline_ts.is_(None), Task.deadline_ts, Task.created_ts)
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(q)
    return list(res.scalars().all())


async def count_tasks_active(session: AsyncSession, user_id: int) -> int:
    q = select(Task).where(Task.user_id == user_id, Task.is_done.is_(False))
    res = await session.execute(q)
    return len(res.scalars().all())


async def mark_done(session: AsyncSession, task_id: int, user_id: int):
    task = await session.get(Task, task_id)
    if task and task.user_id == user_id and not task.is_done:
        task.is_done = True
        task.done_ts = datetime.utcnow()
        await session.flush()
        return True
    return False


async def list_tasks_done(
    session: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
):
    q = (
        select(Task)
        .where(Task.user_id == user_id, Task.is_done.is_(True))
        .order_by(Task.done_ts.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(q)
    return list(res.scalars().all())
