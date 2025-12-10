from aiogram import Router, types
from aiogram.filters import CommandStart
from database.orm import add_user
from keyboards.builders import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "Привет! Я агрегатор вакансий с HH.ru.\n"
        "Нажми кнопку ниже, чтобы начать.",
        reply_markup=main_menu()
    )