import logging
from typing import Dict, Any
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from ..states import BotStates
from .profile import get_user_profile

logger = logging.getLogger(__name__)

# Создаем роутер для базовых обработчиков
basic_router = Router()

@basic_router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.set_state(BotStates.choosing_program)
    
    keyboard = _get_main_keyboard()
    
    # Проверяем, есть ли у пользователя профиль
    user_profile = get_user_profile(message.from_user.id)
    
    if user_profile:
        welcome_text = (
            f"🎓 *Добро пожаловать, {message.from_user.first_name}!*\n\n"
            "Я ваш персональный консультант по магистерским программам ИТМО по ИИ.\n\n"
            "✅ Ваш профиль уже создан\n"
            "🎯 Готов дать персональные рекомендации\n\n"
            "Выберите действие:"
        )
    else:
        welcome_text = (
            f"🎓 *Добро пожаловать, {message.from_user.first_name}!*\n\n"
            "Я помогу вам выбрать подходящую магистерскую программу ИТМО по ИИ и спланировать обучение.\n\n"
            "💡 *Рекомендую начать с создания профиля* - это поможет получить персональные рекомендации по курсам и программам.\n\n"
            "Выберите действие:"
        )
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@basic_router.message(Command("help"))
async def help_handler(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "🤖 *Команды бота:*\n\n"
        "/start - Главное меню\n"
        "/programs - Информация о программах\n"
        "/compare - Сравнить программы\n"
        "/clear - Очистить состояние и вернуться в меню\n"
        "/help - Эта справка\n\n"
        "💬 *Основные функции:*\n"
        "• 📝 Создание профиля для персональных рекомендаций\n"
        "• 📚 Информация о программах обучения\n"
        "• 🎯 Рекомендации по выбору курсов\n"
        "• 📄 Скачивание учебных планов\n"
        "• 🔄 Сравнение программ\n\n"
        "Начните с создания профиля для получения персональных советов!"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

@basic_router.callback_query(F.data == "show_help")
async def show_help_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Помощь'"""
    help_text = (
        "🤖 *Помощь по использованию бота*\n\n"
        "📝 *Мой профиль* - создайте профиль для персональных рекомендаций\n"
        "📚 *Программы* - изучите доступные магистерские программы\n"
        "🔄 *Сравнить программы* - сравните программы между собой\n\n"
        "💡 *Совет:* Создание профиля значительно улучшит качество рекомендаций!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")
    ]])
    
    await callback.message.edit_text(help_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@basic_router.callback_query(F.data == "setup_profile")
async def setup_profile_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Мой профиль'"""
    user_id = callback.from_user.id
    user_profile = get_user_profile(user_id)
    
    if user_profile:
        # Профиль уже существует - показываем его
        await show_existing_profile(callback, user_profile)
    else:
        # Профиля нет - перенаправляем к созданию
        from .profile import start_profile_setup
        await start_profile_setup(callback, state)

async def show_existing_profile(callback: CallbackQuery, profile_data: dict):
    """Показать существующий профиль пользователя"""
    text = (
        f"👤 *Ваш профиль*\n\n"
        f"🎓 *Образование:* {profile_data.get('education_background', 'Не указано')[:50]}{'...' if len(profile_data.get('education_background', '')) > 50 else ''}\n\n"
        f"💼 *Опыт работы:* {profile_data.get('work_experience', 'Не указано')[:50]}{'...' if len(profile_data.get('work_experience', '')) > 50 else ''}\n\n"
        f"🎯 *Интересы:* {', '.join(profile_data.get('interests', []))}\n\n"
        f"🚀 *Цели:* {profile_data.get('career_goals', 'Не указано')[:50]}{'...' if len(profile_data.get('career_goals', '')) > 50 else ''}\n\n"
        f"💻 *Программирование:* {profile_data.get('programming_skills', 'Не указано')[:50]}{'...' if len(profile_data.get('programming_skills', '')) > 50 else ''}\n\n"
        f"🤖 *Опыт с ИИ:* {profile_data.get('ai_experience', 'Не указано')[:50]}{'...' if len(profile_data.get('ai_experience', '')) > 50 else ''}\n\n"
        f"📚 *Предпочтения в обучении:* {', '.join(profile_data.get('learning_preferences', []))}\n\n"
        f"📅 *Создан:* {profile_data.get('created_at', 'Неизвестно')}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Получить рекомендации", callback_data="get_recommendations")],
        [InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="edit_profile")],
        [InlineKeyboardButton(text="🗑 Удалить профиль", callback_data="delete_profile")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@basic_router.callback_query(F.data == "edit_profile")
async def edit_profile_handler(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование профиля"""
    from .profile import start_profile_setup
    await start_profile_setup(callback, state)
    await callback.answer()

@basic_router.callback_query(F.data == "delete_profile")
async def delete_profile_handler(callback: CallbackQuery):
    """Удаление профиля пользователя"""
    user_id = callback.from_user.id
    
    text = (
        "🗑 *Удаление профиля*\n\n"
        "Вы уверены, что хотите удалить свой профиль?\n"
        "Это действие нельзя будет отменить.\n\n"
        "После удаления вы не сможете получать персональные рекомендации."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete_profile")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="setup_profile")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@basic_router.callback_query(F.data == "confirm_delete_profile")
async def confirm_delete_profile_handler(callback: CallbackQuery):
    """Подтверждение удаления профиля"""
    user_id = callback.from_user.id
    
    # Удаляем файл профиля
    profiles_dir = Path(__file__).parent.parent.parent.parent / "data" / "profiles"
    profile_file = profiles_dir / f"user_{user_id}.json"
    
    try:
        if profile_file.exists():
            profile_file.unlink()
            text = "✅ *Профиль успешно удален*\n\nВы можете создать новый профиль в любое время."
        else:
            text = "⚠️ *Профиль не найден*\n\nВозможно, он уже был удален."
    except Exception as e:
        logger.error(f"Ошибка удаления профиля: {e}")
        text = "❌ *Ошибка при удалении профиля*\n\nПопробуйте позже."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать новый профиль", callback_data="setup_profile")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@basic_router.callback_query(F.data == "get_recommendations")
async def get_recommendations_handler(callback: CallbackQuery):
    """Получение персональных рекомендаций"""
    user_id = callback.from_user.id
    user_profile = get_user_profile(user_id)
    
    if not user_profile:
        text = (
            "❌ *Профиль не найден*\n\n"
            "Для получения рекомендаций необходимо создать профиль."
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Создать профиль", callback_data="setup_profile")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
        ])
    else:
        # Генерируем рекомендации на основе профиля
        recommendations = generate_recommendations(user_profile)
        
        text = f"🎯 *Персональные рекомендации*\n\n{recommendations}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Изучить программы", callback_data="show_programs")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="setup_profile")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
        ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

def generate_recommendations(profile: dict) -> str:
    """Генерация рекомендаций на основе профиля"""
    recommendations = []
    
    interests = profile.get('interests', [])
    learning_prefs = profile.get('learning_preferences', [])
    ai_experience = profile.get('ai_experience', '').lower()
    
    # Рекомендации по программе
    if 'Machine Learning' in interests or 'Deep Learning' in interests:
        if 'новичок' in ai_experience or 'не имею' in ai_experience:
            recommendations.append("🎓 *Программа*: Рекомендую \"Искусственный интеллект\" - более фундаментальная подготовка")
        else:
            recommendations.append("🎓 *Программа*: Подходят обе программы, но \"ИИ в продуктах\" может быть интереснее для практики")
    
    # Рекомендации по курсам
    if 'Практика и проекты' in learning_prefs:
        recommendations.append("💻 *Курсы*: Обратите внимание на практические курсы и лабораторные работы")
    
    if 'Теория и лекции' in learning_prefs:
        recommendations.append("📖 *Курсы*: Подойдут теоретические курсы по математическим основам ИИ")
    
    # Рекомендации по подготовке
    programming_skills = profile.get('programming_skills', '').lower()
    if 'python' not in programming_skills:
        recommendations.append("🐍 *Подготовка*: Рекомендую изучить Python - основной язык в области ИИ")
    
    return '\n\n'.join(recommendations) if recommendations else "Анализирую ваш профиль для составления рекомендаций..."

@basic_router.callback_query(F.data == "back_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.set_state(BotStates.choosing_program)
    
    keyboard = _get_main_keyboard()
    
    welcome_text = (
        "🎓 *Главное меню*\n\n"
        "Выберите действие или задайте вопрос:"
    )
    
    await callback.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@basic_router.message(Command("clear"))
async def clear_handler(message: Message, state: FSMContext):
    """Обработчик команды /clear - очистка состояния и возврат в главное меню"""
    await state.clear()
    
    keyboard = _get_main_keyboard()
    
    text = (
        "🔄 *Состояние очищено*\n\n"
        "Все данные сессии удалены. Вы вернулись в главное меню.\n\n"
        "Выберите действие:"
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

def _get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Мой профиль", callback_data="setup_profile")],
        [InlineKeyboardButton(text="📚 Программы", callback_data="show_programs")],
        [InlineKeyboardButton(text="🔄 Сравнить программы", callback_data="compare_programs")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="show_help")]
    ])