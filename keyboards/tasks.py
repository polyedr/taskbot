# app/keyboards/tasks.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def categories_kb(cats: list[str]):
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"cat:{name}")] for name in cats
    ]
    rows.append(
        [InlineKeyboardButton(text="Без категории", callback_data="cat:__none__")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💾 Сохранить", callback_data="task:save")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="task:cancel")],
        ]
    )


def tasks_list_kb(
    tasks: list[tuple[int, str]], page: int, has_next: bool, done_buttons: bool = True
):
    rows = []
    for tid, title in tasks:
        btns = []
        if done_buttons:
            btns.append(
                InlineKeyboardButton(text="✅ Готово", callback_data=f"taskdone:{tid}")
            )
        btns.append(InlineKeyboardButton(text="ℹ️", callback_data=f"taskinfo:{tid}"))
        rows.append(btns)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{page-1}"))
    if has_next:
        nav.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"page:{page+1}")
        )
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)
