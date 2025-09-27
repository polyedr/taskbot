# app/models/task.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user", cascade="all,delete"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user", cascade="all,delete"
    )


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )

    user: Mapped[Optional[User]] = relationship(back_populates="categories")
    tasks: Mapped[list["Task"]] = relationship(back_populates="category")

    __table_args__ = (Index("uq_cat_user_name", "user_id", "name", unique=True),)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text)
    deadline_ts: Mapped[datetime | None] = mapped_column(nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_ts: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    done_ts: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="tasks")
    category: Mapped[Category | None] = relationship(back_populates="tasks")

    __table_args__ = (
        Index("idx_tasks_user_done_deadline", "user_id", "is_done", "deadline_ts"),
    )
