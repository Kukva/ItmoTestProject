# src/bot/telegram_bot.py

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
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
            self.project_root = current_dir.parent.parent.parent
            data_file = self.project_root / "data" / "parsed" / "latest_complete.json"
            
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
        
        # Callback кнопки - ИСПРАВЛЕНО
        self.dp.callback_query(F.data == "show_programs")(self.show_programs_handler)
        self.dp.callback_query(F.data == "show_help")(self.show_help_handler)
        self.dp.callback_query(F.data.startswith("program_"))(self.program_info_handler)
        self.dp.callback_query(F.data.startswith("curriculum_"))(self.curriculum_handler)
        self.dp.callback_query(F.data.startswith("contacts_"))(self.contacts_handler)
        self.dp.callback_query(F.data.startswith("admission_"))(self.admission_handler)
        self.dp.callback_query(F.data.startswith("download_pdf_"))(self.download_pdf_handler)  # НОВОЕ
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
    
    # НОВЫЕ ОБРАБОТЧИКИ CALLBACK'ОВ
    async def show_programs_handler(self, callback: CallbackQuery):
        """Обработчик кнопки 'Программы'"""
        keyboard = self._get_programs_keyboard()
        
        text = (
            "📚 *Выберите программу для подробной информации:*\n\n"
            "🤖 **Искусственный интеллект** - фундаментальная подготовка в области ИИ\n\n"
            "🎯 **ИИ в продуктах** - практическое применение ИИ в продуктах"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    
    async def show_help_handler(self, callback: CallbackQuery):
        """Обработчик кнопки 'Помощь'"""
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
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")
        ]])
        
        await callback.message.edit_text(help_text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    
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
        # Правильно извлекаем program_id
        callback_parts = callback.data.split("_")
        if len(callback_parts) == 2:  # program_ai
            program_id = callback_parts[1]
        else:  # program_ai_product
            program_id = "_".join(callback_parts[1:])  # ai_product
        
        logger.info(f"Выбрана программа: {program_id}")
        
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
    
    # НОВЫЕ ДЕТАЛЬНЫЕ ОБРАБОТЧИКИ
    async def curriculum_handler(self, callback: CallbackQuery):
        """Обработчик учебного плана"""
        # Правильно извлекаем program_id
        callback_parts = callback.data.split("_")
        if len(callback_parts) == 2:  # curriculum_ai
            program_id = callback_parts[1]
        else:  # curriculum_ai_product
            program_id = "_".join(callback_parts[1:])  # ai_product
        
        logger.info(f"Запрошен учебный план для программы: {program_id}")
        
        await self._show_curriculum_menu(callback, program_id, edit_message=True)
        await callback.answer()
    
    async def contacts_handler(self, callback: CallbackQuery):
        """Обработчик контактов"""
        # Правильно извлекаем program_id
        callback_parts = callback.data.split("_")
        if len(callback_parts) == 2:  # contacts_ai
            program_id = callback_parts[1]
        else:  # contacts_ai_product
            program_id = "_".join(callback_parts[1:])  # ai_product
        
        logger.info(f"Запрошены контакты для программы: {program_id}")
        
        contacts_info = self._get_program_contacts(program_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к программе", callback_data=f"program_{program_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
        ])
        
        await callback.message.edit_text(contacts_info, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    
    async def admission_handler(self, callback: CallbackQuery):
        """Обработчик информации о поступлении"""
        # Правильно извлекаем program_id
        callback_parts = callback.data.split("_")
        if len(callback_parts) == 2:  # admission_ai
            program_id = callback_parts[1]
        else:  # admission_ai_product
            program_id = "_".join(callback_parts[1:])  # ai_product
        
        logger.info(f"Запрошена информация о поступлении для программы: {program_id}")
        
        admission_info = self._get_admission_info_detailed(program_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к программе", callback_data=f"program_{program_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
        ])
        
        await callback.message.edit_text(admission_info, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    
    async def download_pdf_handler(self, callback: CallbackQuery):
        """Обработчик скачивания PDF учебного плана"""
        # Правильно извлекаем program_id
        callback_parts = callback.data.split("_")
        if len(callback_parts) == 3:  # download_pdf_ai
            program_id = callback_parts[2]
        else:  # download_pdf_ai_product
            program_id = "_".join(callback_parts[2:])  # ai_product
        
        logger.info(f"Запрошено скачивание PDF для программы: {program_id}")
        
        # Показываем уведомление
        await callback.answer("📄 Отправляю PDF файл...", show_alert=False)
        
        try:
            # Ищем PDF файл
            pdf_path = self._find_pdf_file(program_id)
            
            if not pdf_path or not pdf_path.exists():
                await callback.message.answer("❌ PDF файл учебного плана не найден.")
                return
            
            # Получаем название программы для описания
            program = self.data.get(program_id, {})
            web_data = program.get('web_data', {})
            program_title = web_data.get('program_title', 'Программа')
            
            # Отправляем PDF как документ
            pdf_file = FSInputFile(pdf_path)
            caption = f"📚 Учебный план\n🎓 {program_title}\n📄 Файл: {pdf_path.name}"
            
            await callback.message.answer_document(
                document=pdf_file,
                caption=caption
            )
            
            # Возвращаемся в меню учебного плана (переиспользуем существующий метод)
            await self._show_curriculum_menu(callback, program_id, success_message="✅ PDF файл отправлен!")
            
        except Exception as e:
            logger.error(f"Ошибка отправки PDF: {e}")
            await callback.message.answer("❌ Произошла ошибка при отправке PDF файла.")
    
    async def _show_curriculum_menu(self, callback: CallbackQuery, program_id: str, success_message: str = "", edit_message: bool = False):
        """Показать меню учебного плана (вынесено в отдельный метод)"""
        curriculum_info = self._get_curriculum_info(program_id)
        
        # Проверяем наличие PDF файла
        pdf_available = self._check_pdf_exists(program_id)
        
        # Добавляем предупреждение если PDF нет
        if not pdf_available:
            curriculum_info += "\n⚠️ _PDF файл учебного плана не найден_"
        
        # Добавляем сообщение об успехе если есть
        if success_message:
            curriculum_info += f"\n\n{success_message}"
        
        keyboard_buttons = []
        if pdf_available:
            keyboard_buttons.append([InlineKeyboardButton(text="📄 Скачать PDF", callback_data=f"download_pdf_{program_id}")])
        
        keyboard_buttons.extend([
            [InlineKeyboardButton(text="⬅️ Назад к программе", callback_data=f"program_{program_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        # Редактируем существующее сообщение или отправляем новое
        if edit_message:
            await callback.message.edit_text(
                text=curriculum_info,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer(
                text=curriculum_info,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    
    def _check_pdf_exists(self, program_id: str) -> bool:
        """Проверка существования PDF файла"""
        pdf_path = self._find_pdf_file(program_id)
        return pdf_path is not None and pdf_path.exists()
    
    def _find_pdf_file(self, program_id: str) -> Optional[Path]:
        """Поиск PDF файла для программы"""
        # Папка с PDF файлами
        pdfs_dir = self.project_root / "data" / "pdf"
        
        logger.info(f"Ищем PDF для программы {program_id} в папке: {pdfs_dir}")
        
        if not pdfs_dir.exists():
            logger.warning(f"Папка PDF не найдена: {pdfs_dir}")
            return None
        
        # Простое соответствие program_id -> имя файла
        pdf_filename = f"{program_id}_curriculum.pdf"
        pdf_path = pdfs_dir / pdf_filename
        
        logger.info(f"Ищем файл: {pdf_filename}")
        
        if pdf_path.exists():
            logger.info(f"Найден PDF файл: {pdf_path}")
            return pdf_path
        else:
            logger.warning(f"PDF файл не найден: {pdf_path}")
            return None
    
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
            info += f"• Трудоемкость: {curriculum.get('total_credits', 0)}\n"
            info += f"• Блоков: {len(curriculum.get('blocks', []))}\n\n"
        
        return info
    
    def _get_curriculum_info(self, program_id: str) -> str:
        """Детальная информация об учебном плане"""
        if program_id not in self.data:
            return "❌ Информация о программе не найдена"
        
        program = self.data[program_id]
        web_data = program.get('web_data', {})
        curriculum = program.get('curriculum_data', {})
        
        info = f"📚 *Учебный план - {web_data.get('program_title', 'Программа')}*\n\n"
        
        if not curriculum:
            return info + "❌ Данные учебного плана не загружены"
        
        info += f"📊 *Общая статистика:*\n"
        info += f"• Всего курсов: {curriculum.get('total_courses', 0)}\n"
        info += f"• Кредитов: {curriculum.get('total_credits', 0)}\n"
        info += f"• Блоков обучения: {len(curriculum.get('blocks', []))}\n\n"
        
        # Показываем блоки
        blocks = curriculum.get('blocks', [])
        if blocks:
            info += "📋 *Блоки обучения:*\n"
            for i, block in enumerate(blocks[:5], 1):  # Показываем первые 5 блоков
                info += f"{i}. *{block['name']}*\n"
                info += f"   Трудоемкость: {block['total_credits']} з.ед\n"
                info += f"   Количество часов: {block['total_hours']}\n\n"
            
            if len(blocks) > 5:
                info += f"... и еще {len(blocks) - 5} блоков\n"
        
        return info
    
    def _get_program_contacts(self, program_id: str) -> str:
        """Контактная информация конкретной программы"""
        if program_id not in self.data:
            return "❌ Информация о программе не найдена"
        
        program = self.data[program_id]
        web_data = program.get('web_data', {})
        
        info = f"📞 *Контакты - {web_data.get('program_title', 'Программа')}*\n\n"
        
        manager = web_data.get('manager_name', 'Не указан')
        contacts = web_data.get('manager_contacts', [])
        
        info += f"👤 *Менеджер программы:* {manager}\n\n"
        
        if contacts:
            info += "📧 *Контактные данные:*\n"
            for contact in contacts:
                info += f"• {contact}\n"
        else:
            info += "❌ Контактные данные не указаны\n"
        
        # Общие контакты ИТМО
        info += "\n🏛 *Общие контакты ИТМО:*\n"
        info += "• Сайт: itmo.ru\n"
        info += "• Приемная комиссия: +7 (812) 457-17-35\n"
        info += "• Email: admission@itmo.ru\n"
        
        return info
    
    def _get_admission_info_detailed(self, program_id: str) -> str:
        """Детальная информация о поступлении"""
        if program_id not in self.data:
            return "❌ Информация о программе не найдена"
        
        program = self.data[program_id]
        web_data = program.get('web_data', {})
        
        info = f"🎯 *Поступление - {web_data.get('program_title', 'Программа')}*\n\n"
        
        directions = web_data.get('directions', [])
        if directions:
            info += "📋 *Направления подготовки:*\n\n"
            for direction in directions:
                info += f"*{direction['code']} {direction['name']}*\n"
                info += f"• Бюджетных мест: {direction['budget_places']}\n"
                info += f"• Контрактных мест: {direction['contract_places']}\n"
                
                # Стоимость
                cost = web_data.get('basic_info', {}).get('стоимость контрактного обучения (год)', 'Не указано')
                if cost != 'Не указано':
                    info += f"• Стоимость: {cost}\n"
                
                info += "\n"
        
        # Общая информация о поступлении
        info += "📅 *Важные даты:*\n"
        info += "• Подача документов: июнь-июль\n"
        info += "• Вступительные испытания: июль-август\n"
        info += "• Зачисление: август\n\n"
        
        info += "📝 *Документы:*\n"
        info += "• Диплом бакалавра/специалиста\n"
        info += "• Паспорт\n"
        info += "• Фотографии 3x4\n"
        info += "• Заявление\n"
        
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