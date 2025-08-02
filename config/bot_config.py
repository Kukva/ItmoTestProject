
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния бота
class BotStates(StatesGroup):
    choosing_program = State()
    asking_questions = State()
    comparing_programs = State()

class ITMOBot:
    """Telegram бот для консультаций по программам ИТМО"""
    
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.data = self._load_data()
        self._register_handlers()
    
    def _load_data(self) -> Dict[str, Any]:
        """Загрузка данных программ"""
        try:
            # Путь к данным
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent
            data_file = project_root / "data" / "parsed" / "latest_complete.json"
            
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.error(f"Файл данных не найден: {data_file}")
                return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
            return {}
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        # Команды
        self.dp.message(CommandStart())(self.start_handler)
        self.dp.message(Command("help"))(self.help_handler)
        self.dp.message(Command("programs"))(self.programs_handler)
        self.dp.message(Command("compare"))(self.compare_handler)
        
        # Callback кнопки
        self.dp.callback_query(F.data.startswith("program_"))(self.program_info_handler)
        self.dp.callback_query(F.data == "compare_programs")(self.compare_programs_handler)
        self.dp.callback_query(F.data == "back_main")(self.back_to_main_handler)
        
        # Текстовые сообщения
        self.dp.message(F.text)(self.text_handler)
    
    async def start_handler(self, message: Message, state: FSMContext):
        """Обработчик команды /start"""
        await state.set_state(BotStates.choosing_program)
        
        keyboard = self._get_main_keyboard()
        
        welcome_text = (
            "🎓 *Добро пожаловать в бот ИТМО!*\n\n"
            "Я помогу вам узнать всё о магистерских программах по искусственному интеллекту:\n\n"
            "• Информация о программах\n"
            "• Условия поступления\n"
            "• Учебные планы\n"
            "• Сравнение программ\n\n"
            "Выберите действие:"
        )
        
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
    
    async def help_handler(self, message: Message):
        """Обработчик команды /help"""
        help_text = (
            "🤖 *Команды бота:*\n\n"
            "/start - Главное меню\n"
            "/programs - Информация о программах\n"
            "/compare - Сравнить программы\n"
            "/help - Эта справка\n\n"
            "💬 *Вы можете спросить:*\n"
            "• Стоимость обучения\n"
            "• Сроки поступления\n"
            "• Учебные курсы\n"
            "• Контакты менеджеров\n"
            "• И многое другое!"
        )
        
        await message.answer(help_text, parse_mode="Markdown")
    
    async def programs_handler(self, message: Message):
        """Обработчик команды /programs"""
        keyboard = self._get_programs_keyboard()
        
        text = (
            "📚 *Выберите программу для подробной информации:*\n\n"
            "🤖 **Искусственный интеллект** - фундаментальная подготовка в области ИИ\n\n"
            "🎯 **ИИ в продуктах** - практическое применение ИИ в продуктах"
        )
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    async def compare_handler(self, message: Message):
        """Обработчик команды /compare"""
        comparison = self._compare_programs()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")
        ]])
        
        await message.answer(comparison, reply_markup=keyboard, parse_mode="Markdown")
    
    async def program_info_handler(self, callback: CallbackQuery):
        """Обработчик выбора программы"""
        program_id = callback.data.split("_")[1]
        program_info = self._get_program_info(program_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Учебный план", callback_data=f"curriculum_{program_id}")],
            [InlineKeyboardButton(text="📞 Контакты", callback_data=f"contacts_{program_id}")],
            [InlineKeyboardButton(text="🎯 Поступление", callback_data=f"admission_{program_id}")],
            [InlineKeyboardButton(text="🔄 Сравнить программы", callback_data="compare_programs")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
        ])
        
        await callback.message.edit_text(program_info, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    
    async def compare_programs_handler(self, callback: CallbackQuery):
        """Обработчик сравнения программ"""
        comparison = self._compare_programs()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")
        ]])
        
        await callback.message.edit_text(comparison, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    
    async def back_to_main_handler(self, callback: CallbackQuery, state: FSMContext):
        """Возврат в главное меню"""
        await state.set_state(BotStates.choosing_program)
        
        keyboard = self._get_main_keyboard()
        
        welcome_text = (
            "🎓 *Главное меню*\n\n"
            "Выберите действие или задайте вопрос:"
        )
        
        await callback.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    
    async def text_handler(self, message: Message, state: FSMContext):
        """Обработчик текстовых сообщений"""
        user_question = message.text.lower()
        
        # Простая система ответов на вопросы
        answer = self._get_answer_for_question(user_question)
        
        if answer:
            await message.answer(answer, parse_mode="Markdown")
        else:
            await message.answer(
                "🤔 Извините, я не понял ваш вопрос.\n\n"
                "Попробуйте использовать кнопки меню или задайте вопрос по-другому.\n\n"
                "Например: 'стоимость обучения', 'когда поступать', 'контакты'"
            )
    
    def _get_main_keyboard(self) -> InlineKeyboardMarkup:
        """Главное меню"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Программы", callback_data="show_programs")],
            [InlineKeyboardButton(text="🔄 Сравнить программы", callback_data="compare_programs")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="show_help")]
        ])
    
    def _get_programs_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура выбора программ"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Искусственный интеллект", callback_data="program_ai")],
            [InlineKeyboardButton(text="🎯 ИИ в продуктах", callback_data="program_ai_product")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
        ])
    
    def _get_program_info(self, program_id: str) -> str:
        """Получение информации о программе"""
        if program_id not in self.data:
            return "❌ Информация о программе не найдена"
        
        program = self.data[program_id]
        web_data = program.get('web_data', {})
        curriculum = program.get('curriculum_data', {})
        
        info = f"🎓 *{web_data.get('program_title', 'Программа')}*\n\n"
        
        # Базовая информация
        basic_info = web_data.get('basic_info', {})
        if basic_info:
            info += "📋 *Основная информация:*\n"
            for key, value in basic_info.items():
                if value:
                    info += f"• {key.title()}: {value}\n"
            info += "\n"
        
        # Направления подготовки
        directions = web_data.get('directions', [])
        if directions:
            info += "🎯 *Направления подготовки:*\n"
            for direction in directions:
                info += f"• {direction['code']} {direction['name']}\n"
                info += f"  Бюджет: {direction['budget_places']}, Контракт: {direction['contract_places']}\n"
            info += "\n"
        
        # Учебный план
        if curriculum:
            info += f"📚 *Учебный план:*\n"
            info += f"• Всего курсов: {curriculum.get('total_courses', 0)}\n"
            info += f"• Кредитов: {curriculum.get('total_credits', 0)}\n"
            info += f"• Блоков: {len(curriculum.get('blocks', []))}\n\n"
        
        return info
    
    def _compare_programs(self) -> str:
        """Сравнение программ"""
        if len(self.data) < 2:
            return "❌ Недостаточно данных для сравнения"
        
        ai_data = self.data.get('ai', {}).get('web_data', {})
        ai_product_data = self.data.get('ai_product', {}).get('web_data', {})
        
        comparison = "🔄 *Сравнение программ*\n\n"
        
        # Сравнение стоимости
        ai_cost = ai_data.get('basic_info', {}).get('стоимость контрактного обучения (год)', 'Не указано')
        ai_product_cost = ai_product_data.get('basic_info', {}).get('стоимость контрактного обучения (год)', 'Не указано')
        
        comparison += "💰 *Стоимость:*\n"
        comparison += f"• ИИ: {ai_cost}\n"
        comparison += f"• ИИ в продуктах: {ai_product_cost}\n\n"
        
        # Сравнение направлений
        ai_directions = len(ai_data.get('directions', []))
        ai_product_directions = len(ai_product_data.get('directions', []))
        
        comparison += "🎯 *Направления подготовки:*\n"
        comparison += f"• ИИ: {ai_directions} направлений\n"
        comparison += f"• ИИ в продуктах: {ai_product_directions} направлений\n\n"
        
        # Сравнение учебных планов
        ai_curriculum = self.data.get('ai', {}).get('curriculum_data', {})
        ai_product_curriculum = self.data.get('ai_product', {}).get('curriculum_data', {})
        
        if ai_curriculum and ai_product_curriculum:
            comparison += "📚 *Учебный план:*\n"
            comparison += f"• ИИ: {ai_curriculum.get('total_courses', 0)} курсов\n"
            comparison += f"• ИИ в продуктах: {ai_product_curriculum.get('total_courses', 0)} курсов\n\n"
        
        return comparison
    
    def _get_answer_for_question(self, question: str) -> Optional[str]:
        """Получение ответа на вопрос"""
        # Ключевые слова и соответствующие ответы
        keywords_map = {
            'стоимость': self._get_cost_info,
            'цена': self._get_cost_info,
            'сколько стоит': self._get_cost_info,
            'контакт': self._get_contacts_info,
            'телефон': self._get_contacts_info,
            'email': self._get_contacts_info,
            'менеджер': self._get_contacts_info,
            'поступление': self._get_admission_info,
            'экзамен': self._get_admission_info,
            'когда поступать': self._get_admission_info,
            'курсы': self._get_courses_info,
            'предметы': self._get_courses_info,
            'учебный план': self._get_courses_info,
            'длительность': self._get_duration_info,
            'срок': self._get_duration_info,
            'сколько лет': self._get_duration_info,
        }
        
        for keyword, handler in keywords_map.items():
            if keyword in question:
                return handler()
        
        return None
    
    def _get_cost_info(self) -> str:
        """Информация о стоимости"""
        info = "💰 *Стоимость обучения:*\n\n"
        
        for program_id, program_data in self.data.items():
            web_data = program_data.get('web_data', {})
            title = web_data.get('program_title', program_id)
            cost = web_data.get('basic_info', {}).get('стоимость контрактного обучения (год)', 'Не указано')
            
            info += f"• *{title}*: {cost}\n"
        
        return info
    
    def _get_contacts_info(self) -> str:
        """Контактная информация"""
        info = "📞 *Контакты:*\n\n"
        
        for program_id, program_data in self.data.items():
            web_data = program_data.get('web_data', {})
            title = web_data.get('program_title', program_id)
            manager = web_data.get('manager_name', 'Не указан')
            contacts = web_data.get('manager_contacts', [])
            
            info += f"*{title}:*\n"
            info += f"Менеджер: {manager}\n"
            
            for contact in contacts:
                info += f"• {contact}\n"
            
            info += "\n"
        
        return info
    
    def _get_admission_info(self) -> str:
        """Информация о поступлении"""
        info = "🎯 *Поступление:*\n\n"
        
        for program_id, program_data in self.data.items():
            web_data = program_data.get('web_data', {})
            title = web_data.get('program_title', program_id)
            directions = web_data.get('directions', [])
            
            info += f"*{title}:*\n"
            
            for direction in directions:
                info += f"• {direction['code']} {direction['name']}\n"
                info += f"  Бюджет: {direction['budget_places']} мест\n"
                info += f"  Контракт: {direction['contract_places']} мест\n"
            
            info += "\n"
        
        return info
    
    def _get_courses_info(self) -> str:
        """Информация о курсах"""
        info = "📚 *Учебные планы:*\n\n"
        
        for program_id, program_data in self.data.items():
            web_data = program_data.get('web_data', {})
            curriculum = program_data.get('curriculum_data', {})
            title = web_data.get('program_title', program_id)
            
            info += f"*{title}:*\n"
            
            if curriculum:
                info += f"• Всего курсов: {curriculum.get('total_courses', 0)}\n"
                info += f"• Кредитов: {curriculum.get('total_credits', 0)}\n"
                
                blocks = curriculum.get('blocks', [])
                if blocks:
                    info += "• Основные блоки:\n"
                    for block in blocks[:3]:  # Показываем первые 3 блока
                        info += f"  - {block['name']} ({block['total_credits']} зет)\n"
            else:
                info += "• Данные учебного плана загружаются...\n"
            
            info += "\n"
        
        return info
    
    def _get_duration_info(self) -> str:
        """Информация о длительности"""
        info = "⏱ *Длительность обучения:*\n\n"
        
        for program_id, program_data in self.data.items():
            web_data = program_data.get('web_data', {})
            title = web_data.get('program_title', program_id)
            duration = web_data.get('basic_info', {}).get('длительность', 'Не указано')
            
            info += f"• *{title}*: {duration}\n"
        
        return info
    
    async def start_polling(self):
        """Запуск бота"""
        logger.info("Бот запущен!")
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Остановка бота"""
        await self.bot.session.close()

# Точка входа
async def main():
    # Токен бота (получить у @BotFather)
    TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Установите токен бота в переменной TOKEN")
        return
    
    bot = ITMOBot(TOKEN)
    
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        print("Остановка бота...")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())