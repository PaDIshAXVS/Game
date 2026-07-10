import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from core import User, Session, setup
import os
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('TOKEN')


bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    session = Session()

    user = User.load(session, message.from_user.id)

    app_button = KeyboardButton(
        text='Открыть приложение',
        web_app=WebAppInfo(url=f'https://talon-geography-shape.ngrok-free.dev/user/{message.from_user.id}')
    )

    keyboard = ReplyKeyboardMarkup(keyboard=[[app_button]], resize_keyboard=True)

    await message.answer(
        f'Привет, {message.from_user.first_name}!',
        reply_markup=keyboard
    )

    session.close()


async def main():
    setup()

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())