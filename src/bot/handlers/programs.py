import logging
from pathlib import Path
from typing import Dict, Any, Optional

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..states import BotStates

logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков программ
programs_router = Router()

@programs_router.message(Command("programs"))
async def programs_handler(message: Message):
    """Обработчик команды /programs"""
    keyboard = _get_programs_keyboard()
    
    text = (
        "📚 *Выберите программу для подробной информации:*\n\n"
        "🤖 **Искусственный интеллект** - фундаментальная подготовка в области ИИ\n\n"
        "🎯 **ИИ в продуктах** - практическое применение ИИ в продуктах"
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@programs_router.message(Command("compare"))
async def compare_handler(message: Message, bot_instance):
    """Обработчик команды /compare"""
    comparison = bot_instance._compare_programs()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")
    ]])
    
    await message.answer(comparison, reply_markup=keyboard, parse_mode="Markdown")

@programs_router.callback_query(F.data == "show_programs")
async def show_programs_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Программы'"""
    keyboard = _get_programs_keyboard()
    
    text = (
        "📚 *Выберите программу для подробной информации:*\n\n"
        "🤖 **Искусственный интеллект** - фундаментальная подготовка в области ИИ\n\n"
        "🎯 **ИИ в продуктах** - практическое применение ИИ в продуктах"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@programs_router.callback_query(F.data == "compare_programs")
async def compare_programs_handler(callback: CallbackQuery, bot_instance):
    """Обработчик сравнения программ"""
    comparison = bot_instance._compare_programs()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")
    ]])
    
    await callback.message.edit_text(comparison, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@programs_router.callback_query(F.data.startswith("program_"))
async def program_info_handler(callback: CallbackQuery, bot_instance):
    """Обработчик выбора программы"""
    # Правильно извлекаем program_id
    callback_parts = callback.data.split("_")
    if len(callback_parts) == 2:  # program_ai
        program_id = callback_parts[1]
    else:  # program_ai_product
        program_id = "_".join(callback_parts[1:])  # ai_product
    
    logger.info(f"Выбрана программа: {program_id}")
    
    program_info = bot_instance._get_program_info(program_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Учебный план", callback_data=f"curriculum_{program_id}")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data=f"contacts_{program_id}")],
        [InlineKeyboardButton(text="🎯 Поступление", callback_data=f"admission_{program_id}")],
        [InlineKeyboardButton(text="🔄 Сравнить программы", callback_data="compare_programs")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(program_info, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@programs_router.callback_query(F.data.startswith("curriculum_"))
async def curriculum_handler(callback: CallbackQuery, bot_instance):
    """Обработчик учебного плана"""
    # Правильно извлекаем program_id
    callback_parts = callback.data.split("_")
    if len(callback_parts) == 2:  # curriculum_ai
        program_id = callback_parts[1]
    else:  # curriculum_ai_product
        program_id = "_".join(callback_parts[1:])  # ai_product
    
    logger.info(f"Запрошен учебный план для программы: {program_id}")
    
    await bot_instance._show_curriculum_menu(callback, program_id, edit_message=True)
    await callback.answer()

@programs_router.callback_query(F.data.startswith("contacts_"))
async def contacts_handler(callback: CallbackQuery, bot_instance):
    """Обработчик контактов"""
    # Правильно извлекаем program_id
    callback_parts = callback.data.split("_")
    if len(callback_parts) == 2:  # contacts_ai
        program_id = callback_parts[1]
    else:  # contacts_ai_product
        program_id = "_".join(callback_parts[1:])  # ai_product
    
    logger.info(f"Запрошены контакты для программы: {program_id}")
    
    contacts_info = bot_instance._get_program_contacts(program_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к программе", callback_data=f"program_{program_id}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(contacts_info, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@programs_router.callback_query(F.data.startswith("admission_"))
async def admission_handler(callback: CallbackQuery, bot_instance):
    """Обработчик информации о поступлении"""
    # Правильно извлекаем program_id
    callback_parts = callback.data.split("_")
    if len(callback_parts) == 2:  # admission_ai
        program_id = callback_parts[1]
    else:  # admission_ai_product
        program_id = "_".join(callback_parts[1:])  # ai_product
    
    logger.info(f"Запрошена информация о поступлении для программы: {program_id}")
    
    admission_info = bot_instance._get_admission_info_detailed(program_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к программе", callback_data=f"program_{program_id}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(admission_info, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@programs_router.callback_query(F.data.startswith("download_pdf_"))
async def download_pdf_handler(callback: CallbackQuery, bot_instance):
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
        pdf_path = bot_instance._find_pdf_file(program_id)
        
        if not pdf_path or not pdf_path.exists():
            await callback.message.answer("❌ PDF файл учебного плана не найден.")
            return
        
        # Получаем название программы для описания
        program = bot_instance.data.get(program_id, {})
        web_data = program.get('web_data', {})
        program_title = web_data.get('program_title', 'Программа')
        
        # Отправляем PDF как документ
        pdf_file = FSInputFile(pdf_path)
        caption = f"📚 Учебный план\n🎓 {program_title}\n📄 Файл: {pdf_path.name}"
        
        await callback.message.answer_document(
            document=pdf_file,
            caption=caption
        )
        
        # Возвращаемся в меню учебного плана
        await bot_instance._show_curriculum_menu(callback, program_id, success_message="✅ PDF файл отправлен!")
        
    except Exception as e:
        logger.error(f"Ошибка отправки PDF: {e}")
        await callback.message.answer("❌ Произошла ошибка при отправке PDF файла.")

def _get_programs_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора программ"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Искусственный интеллект", callback_data="program_ai")],
        [InlineKeyboardButton(text="🎯 ИИ в продуктах", callback_data="program_ai_product")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
    ])