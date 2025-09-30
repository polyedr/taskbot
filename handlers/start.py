from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.main import MAIN_MENU, START_TEXT

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    # ... дальше некоторая логика ...
    await message.answer(START_TEXT, reply_markup=MAIN_MENU)
