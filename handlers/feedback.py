# handlers/feedback.py
from __future__ import annotations

from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)

from config import ADMINS
from keyboards.main import MAIN_MENU
from models.db import get_sessionmaker
from models.feedback import Feedback

router = Router()


# ================== Keyboards ==================
def feedback_start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐞 Баг", callback_data="fb:cat:bug")],
            [
                InlineKeyboardButton(
                    text="💡 Идея/предложение", callback_data="fb:cat:idea"
                )
            ],
            [InlineKeyboardButton(text="🗣 Отзыв", callback_data="fb:cat:review")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="fb:cancel")],
        ]
    )


def feedback_attach_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить скрин", callback_data="fb:add_screenshot"
                )
            ],
            [InlineKeyboardButton(text="✅ Отправить", callback_data="fb:send")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="fb:cancel")],
        ]
    )


# ================== FSM ==================
class FeedbackStates(StatesGroup):
    choosing_category = State()
    typing_text = State()
    waiting_screenshot = State()
    confirm_send = State()


# ================== Helpers ==================
def human_cat(cat: str) -> str:
    return {"bug": "Баг/ошибка", "idea": "Идея/предложение", "review": "Отзыв"}.get(
        cat, cat
    )


def parse_admin_ids(raw) -> list[int]:
    out: list[int] = []
    for x in raw or []:
        s = str(x).strip()
        if not s:
            continue
        try:
            out.append(int(s))
        except ValueError:
            pass
    return list(dict.fromkeys(out))


async def safe_send_message(bot: Bot, chat_id: int, *args, **kwargs) -> bool:
    try:
        await bot.send_message(chat_id, *args, **kwargs)
        return True
    except TelegramBadRequest:
        return False


async def safe_send_photo(bot: Bot, chat_id: int, *args, **kwargs) -> bool:
    try:
        await bot.send_photo(chat_id, *args, **kwargs)
        return True
    except TelegramBadRequest:
        return False


async def _clear_inline(cb: CallbackQuery):
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass


# ================== Entry ==================
@router.message(F.text.casefold() == "✉️ обратная связь".casefold())
@router.message(F.command("feedback"))
async def feedback_entry(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(FeedbackStates.choosing_category)
    await message.answer("Выберите тип сообщения:", reply_markup=feedback_start_kb())


# ================== Choose category ==================
@router.callback_query(F.data.startswith("fb:cat:"))
async def feedback_choose_category(cb: CallbackQuery, state: FSMContext):
    await _clear_inline(cb)
    cat = cb.data.split(":")[-1]  # bug | idea | review
    await state.update_data(category=cat)
    await state.set_state(FeedbackStates.typing_text)
    await cb.message.answer(
        "Опишите проблему/идею/отзыв одним сообщением.\n\n"
        "Можно приложить скриншот на следующем шаге.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await cb.answer()


# ================== Cancel ==================
@router.callback_query(F.data == "fb:cancel")
async def feedback_cancel(cb: CallbackQuery, state: FSMContext):
    await _clear_inline(cb)
    await state.clear()
    await cb.message.answer("Отменено. Спасибо!", reply_markup=MAIN_MENU)
    await cb.answer()


# ================== Text input ==================
@router.message(FeedbackStates.typing_text, F.text)
async def feedback_text(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    if len(txt) < 10:
        await message.answer("Коротко. Пожалуйста, опишите подробнее (от 10 символов).")
        return
    await state.update_data(text=txt, screenshots=[])
    await state.set_state(FeedbackStates.confirm_send)
    await message.answer(
        "Принято. Хотите добавить скриншот(ы)? Если да — нажмите «Добавить скрин», "
        "или сразу отправьте без вложений.",
        reply_markup=feedback_attach_kb(),
    )


# ================== Add screenshot ==================
@router.callback_query(FeedbackStates.confirm_send, F.data == "fb:add_screenshot")
async def feedback_wait_screenshot(cb: CallbackQuery, state: FSMContext):
    await _clear_inline(cb)
    await state.set_state(FeedbackStates.waiting_screenshot)
    await cb.message.answer(
        "Пришлите фото/скрин (как фото или как файл). Когда закончите — нажмите «Отправить».",
        reply_markup=feedback_attach_kb(),
    )
    await cb.answer()


# ================== Receive screenshot ==================
@router.message(FeedbackStates.waiting_screenshot, F.photo | F.document)
async def feedback_collect_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    screenshots: list[str] = data.get("screenshots", [])

    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id

    if file_id:
        screenshots.append(file_id)
        await state.update_data(screenshots=screenshots)
        await message.answer(
            f"Скрин добавлен. Всего: {len(screenshots)}",
            reply_markup=feedback_attach_kb(),
        )
    else:
        await message.answer(
            "Не похоже на изображение/файл. Пришлите картинку или файл."
        )


# ================== Send ==================
@router.callback_query(FeedbackStates.confirm_send, F.data == "fb:send")
@router.callback_query(FeedbackStates.waiting_screenshot, F.data == "fb:send")
async def feedback_send(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await _clear_inline(cb)
    data = await state.get_data()
    cat: str = data.get("category", "unknown")
    text: str = data.get("text", "")
    screenshots: list[str] = data.get("screenshots", [])
    user = cb.from_user

    # 1) save to DB (SQLAlchemy)
    Session = get_sessionmaker()
    async with Session() as session:
        fb = Feedback(
            user_id=user.id,
            username=user.username or "",
            category=cat,
            text=text,
        )
        session.add(fb)
        await session.commit()

    # 2) send to admins
    caption = (
        f"🆕 <b>Обратная связь</b>\n"
        f"Категория: <b>{human_cat(cat)}</b>\n"
        f"От: @{user.username or '—'} (ID: <code>{user.id}</code>)\n"
        f"Время: {datetime.now():%d.%m.%Y %H:%M}\n\n"
        f"<b>Текст:</b>\n{text}"
    )
    admin_ids = parse_admin_ids(ADMINS)

    if not admin_ids:
        # Если не настроены админы, завершаем, сообщив пользователю об успехе
        pass
    elif not screenshots:
        for admin_id in admin_ids:
            await safe_send_message(bot, admin_id, caption, parse_mode=ParseMode.HTML)
    else:
        for admin_id in admin_ids:
            ok = await safe_send_photo(
                bot,
                admin_id,
                screenshots[0],
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
            if ok:
                for file_id in screenshots[1:]:
                    await safe_send_photo(bot, admin_id, file_id)

    # 3) user reply
    await state.clear()
    await cb.message.answer(
        "Спасибо! Сообщение отправлено. Мы вернёмся с ответом при необходимости.",
        reply_markup=MAIN_MENU,
    )
    await cb.answer()
