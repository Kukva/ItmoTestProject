# src/bot/telegram_bot.py

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .handlers import basic_router, profile_router, programs_router, text_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        """Регистрация роутеров"""
        # Подключаем экземпляр бота к каждому роутеру через middleware
        self.dp.message.middleware.register(self._add_bot_instance)
        self.dp.callback_query.middleware.register(self._add_bot_instance)
        
        # Регистрируем роутеры в правильном порядке
        self.dp.include_router(basic_router)
        self.dp.include_router(profile_router)
        self.dp.include_router(programs_router)
        self.dp.include_router(text_router)  # Последним, как fallback
    
    async def _add_bot_instance(self, handler, event, data):
        """Middleware для передачи экземпляра бота в обработчики"""
        data['bot_instance'] = self
        return await handler(event, data)
    
    # Методы для работы с данными (используются в обработчиках)
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
    
    def _find_pdf_file(self, program_id: str) -> Optional[Path]:
        """Поиск PDF файла для программы"""
        pdfs_dir = self.project_root / "data" / "pdf"
        
        if not pdfs_dir.exists():
            logger.warning(f"Папка PDF не найдена: {pdfs_dir}")
            return None
        
        pdf_filename = f"{program_id}_curriculum.pdf"
        pdf_path = pdfs_dir / pdf_filename
        
        return pdf_path if pdf_path.exists() else None
    
    async def _show_curriculum_menu(self, callback, program_id: str, success_message: str = "", edit_message: bool = False):
        """Показать меню учебного плана"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        curriculum_info = self._get_curriculum_info(program_id)
        
        # Проверяем наличие PDF файла
        pdf_available = self._find_pdf_file(program_id) is not None
        
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
    
    # Методы для ответов на вопросы (используются в text.py)
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