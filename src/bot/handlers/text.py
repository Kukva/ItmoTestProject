import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

# Создаем роутер для обработки текстовых сообщений
text_router = Router()

@text_router.message(F.text)
async def text_handler(message: Message, state: FSMContext, bot_instance):
    """Обработчик текстовых сообщений"""
    user_question = message.text.lower()
    
    # Простая система ответов на вопросы
    answer = _get_answer_for_question(user_question, bot_instance)
    
    if answer:
        await message.answer(answer, parse_mode="Markdown")
    else:
        await message.answer(
            "🤔 Извините, я не понял ваш вопрос.\n\n"
            "Попробуйте использовать кнопки меню или задайте вопрос по-другому.\n\n"
            "💡 *Рекомендую создать профиль* - это поможет получить более точные ответы!\n\n"
            "*Примеры вопросов:*\n"
            "• \"стоимость обучения\"\n"
            "• \"когда поступать\"\n"
            "• \"контакты менеджера\"\n"
            "• \"какие курсы изучать\""
        )

def _get_answer_for_question(question: str, bot_instance) -> Optional[str]:
    """Получение ответа на вопрос"""
    # Ключевые слова и соответствующие ответы
    keywords_map = {
        'стоимость': lambda: bot_instance._get_cost_info(),
        'цена': lambda: bot_instance._get_cost_info(),
        'сколько стоит': lambda: bot_instance._get_cost_info(),
        'контакт': lambda: bot_instance._get_contacts_info(),
        'телефон': lambda: bot_instance._get_contacts_info(),
        'email': lambda: bot_instance._get_contacts_info(),
        'менеджер': lambda: bot_instance._get_contacts_info(),
        'поступление': lambda: bot_instance._get_admission_info(),
        'экзамен': lambda: bot_instance._get_admission_info(),
        'когда поступать': lambda: bot_instance._get_admission_info(),
        'курсы': lambda: bot_instance._get_courses_info(),
        'предметы': lambda: bot_instance._get_courses_info(),
        'учебный план': lambda: bot_instance._get_courses_info(),
        'длительность': lambda: bot_instance._get_duration_info(),
        'срок': lambda: bot_instance._get_duration_info(),
        'сколько лет': lambda: bot_instance._get_duration_info(),
        'профиль': lambda: _get_profile_help(),
        'рекомендации': lambda: _get_recommendations_help(),
        'помощь': lambda: _get_general_help(),
    }
    
    for keyword, handler in keywords_map.items():
        if keyword in question:
            return handler()
    
    return None

def _get_profile_help() -> str:
    """Помощь по профилю"""
    return (
        "📝 *Профиль пользователя*\n\n"
        "Создание профиля поможет получить:\n"
        "• 🎯 Персональные рекомендации курсов\n"
        "• 📚 Подходящую программу обучения\n"
        "• 🎓 План изучения дисциплин\n\n"
        "Нажмите *\"📝 Мой профиль\"* в главном меню для создания!"
    )

def _get_recommendations_help() -> str:
    """Помощь по рекомендациям"""
    return (
        "🎯 *Персональные рекомендации*\n\n"
        "Для получения рекомендаций необходимо:\n"
        "1. 📝 Создать профиль (ответить на 7 вопросов)\n"
        "2. 🎯 Нажать \"Получить рекомендации\"\n\n"
        "Я подберу подходящие курсы на основе:\n"
        "• Вашего образования и опыта\n"
        "• Интересов в области ИИ\n"
        "• Карьерных целей\n"
        "• Предпочтений в обучении"
    )

def _get_general_help() -> str:
    """Общая помощь"""
    return (
        "🤖 *Как я могу помочь:*\n\n"
        "📝 *Мой профиль* - создайте персональный профиль\n"
        "📚 *Программы* - изучите магистерские программы\n"
        "🔄 *Сравнение* - сравните программы между собой\n"
        "🎯 *Рекомендации* - получите персональные советы\n\n"
        "*Популярные вопросы:*\n"
        "• Стоимость обучения\n"
        "• Сроки поступления\n"
        "• Контакты менеджеров\n"
        "• Учебные планы и курсы"
    )