import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import config
from database.orm import init_db
from handlers.common import router as common_router
from handlers.search import router as search_router

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация БД
    await init_db()
    
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_router(common_router)
    dp.include_router(search_router)
    
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")