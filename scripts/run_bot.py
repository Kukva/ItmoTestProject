# scripts/run_bot.py

import asyncio
import os
import sys
from pathlib import Path

# Загрузка .env файла
from dotenv import load_dotenv
load_dotenv()

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.bot.telegram_bot import ITMOBot

async def main():
    """Запуск Telegram бота"""
    
    # Получаем токен из переменной окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ Токен бота не найден!")
        print("Установите переменную окружения TELEGRAM_BOT_TOKEN")
        print("Или создайте файл .env с содержимым:")
        print("TELEGRAM_BOT_TOKEN=your_token_here")
        print("\nПолучить токен: https://t.me/BotFather")
        return
    
    print("🤖 Запуск Telegram бота ИТМО...")
    print("Нажмите Ctrl+C для остановки")
    
    bot = ITMOBot(token)
    
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.stop()
        print("✅ Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())