# middlewares/anti_spam_simple.py
from __future__ import annotations

import time
from typing import Dict, Iterable, Optional

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class CooldownMiddleware(BaseMiddleware):
    """
    Простой кулдаун на пользователя:
      - cooldown: минимальный интервал (секунды) между событиями
      - whitelist: ID, на кого антиспам не действует
      - reply_text: сообщение пользователю при превышении лимита
    """

    def __init__(
        self,
        cooldown: float = 1.0,
        whitelist: Optional[Iterable[int]] = None,
        reply_text: str = "Слишком часто. Подождите немного…",
    ):
        super().__init__()
        self.cooldown = max(0.1, cooldown)
        self.whitelist = set(int(x) for x in (whitelist or []))
        self.reply_text = reply_text
        self._last: Dict[int, float] = {}  # user_id -> last ts

    def _uid(self, event: TelegramObject) -> Optional[int]:
        user = getattr(event, "from_user", None)
        return getattr(user, "id", None) if user else None

    async def __call__(self, handler, event: TelegramObject, data: dict):
        uid = self._uid(event)
        if uid is None or uid in self.whitelist:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last.get(uid, 0.0)
        if now - last < self.cooldown:
            # Останавливаем событие, уведомляем пользователя
            if isinstance(event, Message):
                try:
                    await event.answer(self.reply_text)
                except Exception:
                    pass
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer(self.reply_text, show_alert=False)
                except Exception:
                    pass
            return  # не вызываем handler

        self._last[uid] = now
        return await handler(event, data)
