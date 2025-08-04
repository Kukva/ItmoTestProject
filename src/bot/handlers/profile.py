import json
import logging
from pathlib import Path
from typing import Dict, Any

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from ..states import ProfileSetup

logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков профиля
profile_router = Router()

# Путь для сохранения профилей (временно в JSON)
PROFILES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)

@profile_router.callback_query(F.data == "setup_profile")
async def start_profile_setup(callback: CallbackQuery, state: FSMContext):
    """Начало настройки профиля"""
    await state.set_state(ProfileSetup.education_background)
    
    text = (
        "📝 *Создание вашего профиля*\n\n"
        "Давайте соберем информацию о вас, чтобы дать персональные рекомендации по выбору программы и курсов.\n\n"
        "🎓 *Вопрос 1 из 7*\n\n"
        "Расскажите о вашем образовательном бэкграунде:\n"
        "• Какую специальность изучаете/изучали?\n"
        "• В какой области у вас есть диплом?\n\n"
        "_Например: \"Бакалавр информатики, специализация - разработка ПО\"_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profile")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
@profile_router.message(StateFilter(ProfileSetup.education_background))
async def process_education_background(message: Message, state: FSMContext):
    """Обработка информации об образовании"""
    await state.update_data(education_background=message.text)
    await state.set_state(ProfileSetup.work_experience)
    
    text = (
        "✅ Отлично!\n\n"
        "💼 *Вопрос 2 из 7*\n\n"
        "Расскажите о вашем опыте работы:\n"
        "• В какой сфере работаете/работали?\n" 
        "• Какую должность занимаете?\n"
        "• Сколько лет опыта?\n\n"
        "_Например: \"3 года Python-разработчиком в финтех компании\"_\n"
        "_Или: \"Пока не работал, только учусь\"_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_education")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profile")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@profile_router.message(StateFilter(ProfileSetup.work_experience))
async def process_work_experience(message: Message, state: FSMContext):
    """Обработка опыта работы"""
    await state.update_data(work_experience=message.text)
    await state.set_state(ProfileSetup.interests)
    
    # Инициализируем пустой список выбранных интересов
    await state.update_data(selected_interests=[])
    
    await show_interests_menu(message, state, is_new_message=True)

async def show_interests_menu(message_or_callback, state: FSMContext, is_new_message: bool = False):
    """Показать меню выбора интересов с визуальной индикацией"""
    data = await state.get_data()
    selected_interests = data.get('selected_interests', [])
    
    text = (
        "✅ Понятно!\n\n"
        "🎯 *Вопрос 3 из 7*\n\n"
        "Какие области искусственного интеллекта вас больше всего интересуют?\n"
        "Выберите несколько вариантов:\n\n"
    )
    
    # Добавляем информацию о выбранных интересах
    if selected_interests:
        text += f"✅ *Выбрано ({len(selected_interests)}):* {', '.join(selected_interests)}\n\n"
    else:
        text += "❌ *Пока ничего не выбрано*\n\n"
    
    # Создаем кнопки с визуальной индикацией
    interest_buttons = [
        ("🤖 Machine Learning", "interest_ml", "Machine Learning"),
        ("🧠 Deep Learning", "interest_dl", "Deep Learning"),
        ("👁 Computer Vision", "interest_cv", "Computer Vision"),
        ("💬 NLP", "interest_nlp", "Natural Language Processing"),
        ("🔍 Data Science", "interest_ds", "Data Science"),
        ("🎮 Reinforcement Learning", "interest_rl", "Reinforcement Learning"),
        ("⚡ MLOps", "interest_mlops", "MLOps"),
        ("📊 Business Analytics", "interest_ba", "Business Analytics")
    ]
    
    keyboard_buttons = []
    for button_text, callback_data, interest_name in interest_buttons:
        # Добавляем галочку если интерес выбран
        if interest_name in selected_interests:
            display_text = f"✅ {button_text}"
        else:
            display_text = f"⚪ {button_text}"
        
        keyboard_buttons.append([InlineKeyboardButton(text=display_text, callback_data=callback_data)])
    
    # Добавляем кнопки управления
    keyboard_buttons.extend([
        [InlineKeyboardButton(text="✅ Готово", callback_data="interest_done")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_work")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profile")]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if is_new_message:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message_or_callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@profile_router.callback_query(F.data.startswith("interest_"))
async def process_interest_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора интересов"""
    if callback.data == "interest_done":
        # Переходим к следующему вопросу
        data = await state.get_data()
        selected_interests = data.get('selected_interests', [])
        
        if not selected_interests:
            await callback.answer("⚠️ Выберите хотя бы одну область интересов", show_alert=True)
            return
        
        await state.update_data(interests=selected_interests)
        await state.set_state(ProfileSetup.career_goals)
        
        text = (
            "✅ Отличный выбор!\n\n"
            "🎯 *Вопрос 4 из 7*\n\n"
            "Какие у вас карьерные цели? Кем видите себя через 2-3 года?\n\n"
            "_Например: \"Хочу стать ML-инженером в крупной IT-компании\" или \"Планирую открыть свой ИИ-стартап\"_"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_interests")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profile")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
        return
    
    # Добавляем/убираем интерес из списка
    interest_map = {
        "interest_ml": "Machine Learning",
        "interest_dl": "Deep Learning", 
        "interest_cv": "Computer Vision",
        "interest_nlp": "Natural Language Processing",
        "interest_ds": "Data Science",
        "interest_rl": "Reinforcement Learning",
        "interest_mlops": "MLOps",
        "interest_ba": "Business Analytics"
    }
    
    interest_name = interest_map.get(callback.data)
    if not interest_name:
        await callback.answer("❌ Неизвестный интерес")
        return
    
    data = await state.get_data()
    selected_interests = data.get('selected_interests', [])
    
    if interest_name in selected_interests:
        selected_interests.remove(interest_name)
        await callback.answer(f"❌ Убрали: {interest_name}")
    else:
        selected_interests.append(interest_name)
        await callback.answer(f"✅ Добавили: {interest_name}")
    
    await state.update_data(selected_interests=selected_interests)
    
    # Обновляем интерфейс
    await show_interests_menu(callback, state, is_new_message=False)

@profile_router.callback_query(F.data == "back_to_interests")
async def back_to_interests(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору интересов"""
    await state.set_state(ProfileSetup.interests)
    await show_interests_menu(callback, state, is_new_message=False)
    await callback.answer()

@profile_router.message(StateFilter(ProfileSetup.career_goals))
async def process_career_goals(message: Message, state: FSMContext):
    """Обработка карьерных целей"""
    await state.update_data(career_goals=message.text)
    await state.set_state(ProfileSetup.programming_skills)
    
    text = (
        "✅ Амбициозно!\n\n"
        "💻 *Вопрос 5 из 7*\n\n"
        "Какими языками программирования владеете?\n"
        "Укажите уровень владения:\n\n"
        "_Например: \"Python (хорошо), JavaScript (базовый), C++ (изучаю)\"_\n"
        "_Или: \"Пока не программирую, планирую изучать\"_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_goals")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profile")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@profile_router.message(StateFilter(ProfileSetup.programming_skills))
async def process_programming_skills(message: Message, state: FSMContext):
    """Обработка навыков программирования"""
    await state.update_data(programming_skills=message.text)
    await state.set_state(ProfileSetup.ai_experience)
    
    text = (
        "✅ Понятно!\n\n"
        "🤖 *Вопрос 6 из 7*\n\n"
        "Какой у вас опыт с искусственным интеллектом и машинным обучением?\n\n"
        "_Например: \"Проходил онлайн-курсы по ML, делал пет-проекты\" или \"Полный новичок в ИИ\"_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_programming")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profile")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@profile_router.message(StateFilter(ProfileSetup.ai_experience))
async def process_ai_experience(message: Message, state: FSMContext):
    """Обработка опыта с ИИ"""
    await state.update_data(ai_experience=message.text)
    await state.set_state(ProfileSetup.learning_preferences)
    
    # Инициализируем пустой список предпочтений в обучении
    await state.update_data(learning_preferences=[])
    
    await show_learning_preferences_menu(message, state, is_new_message=True)

async def show_learning_preferences_menu(message_or_callback, state: FSMContext, is_new_message: bool = False):
    """Показать меню предпочтений в обучении с визуальной индикацией"""
    data = await state.get_data()
    learning_preferences = data.get('learning_preferences', [])
    
    text = (
        "✅ Хорошо!\n\n"
        "📚 *Вопрос 7 из 7*\n\n"
        "Как вам больше нравится учиться?\n"
        "Выберите предпочтительные форматы:\n\n"
    )
    
    # Добавляем информацию о выбранных предпочтениях
    if learning_preferences:
        text += f"✅ *Выбрано ({len(learning_preferences)}):* {', '.join(learning_preferences)}\n\n"
    else:
        text += "❌ *Пока ничего не выбрано*\n\n"
    
    # Создаем кнопки с визуальной индикацией
    learning_buttons = [
        ("📖 Теория и лекции", "learn_theory", "Теория и лекции"),
        ("💻 Практика и проекты", "learn_practice", "Практика и проекты"),
        ("👥 Групповая работа", "learn_group", "Групповая работа"),
        ("🔬 Исследовательская работа", "learn_research", "Исследовательская работа"),
        ("🏢 Связь с индустрией", "learn_industry", "Связь с индустрией")
    ]
    
    keyboard_buttons = []
    for button_text, callback_data, pref_name in learning_buttons:
        # Добавляем галочку если предпочтение выбрано
        if pref_name in learning_preferences:
            display_text = f"✅ {button_text}"
        else:
            display_text = f"⚪ {button_text}"
        
        keyboard_buttons.append([InlineKeyboardButton(text=display_text, callback_data=callback_data)])
    
    # Добавляем кнопки управления
    keyboard_buttons.extend([
        [InlineKeyboardButton(text="✅ Готово", callback_data="learn_done")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_ai_exp")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profile")]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if is_new_message:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message_or_callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@profile_router.callback_query(F.data.startswith("learn_"))
async def process_learning_preferences(callback: CallbackQuery, state: FSMContext):
    """Обработка предпочтений в обучении"""
    if callback.data == "learn_done":
        # Переходим к подтверждению профиля  
        data = await state.get_data()
        learning_prefs = data.get('learning_preferences', [])
        
        if not learning_prefs:
            await callback.answer("⚠️ Выберите хотя бы один формат обучения", show_alert=True)
            return
        
        await state.set_state(ProfileSetup.profile_confirmation)
        await show_profile_summary(callback, state)
        return
    
    # Добавляем/убираем предпочтение
    learning_map = {
        "learn_theory": "Теория и лекции",
        "learn_practice": "Практика и проекты",
        "learn_group": "Групповая работа", 
        "learn_research": "Исследовательская работа",
        "learn_industry": "Связь с индустрией"
    }
    
    pref_name = learning_map.get(callback.data)
    if not pref_name:
        await callback.answer("❌ Неизвестное предпочтение")
        return
    
    data = await state.get_data()
    learning_prefs = data.get('learning_preferences', [])
    
    if pref_name in learning_prefs:
        learning_prefs.remove(pref_name)
        await callback.answer(f"❌ Убрали: {pref_name}")
    else:
        learning_prefs.append(pref_name)
        await callback.answer(f"✅ Добавили: {pref_name}")
    
    await state.update_data(learning_preferences=learning_prefs)
    
    # Обновляем интерфейс
    await show_learning_preferences_menu(callback, state, is_new_message=False)

@profile_router.callback_query(F.data == "back_to_ai_exp")
async def back_to_ai_exp(callback: CallbackQuery, state: FSMContext):
    """Возврат к вопросу об опыте с ИИ"""
    await state.set_state(ProfileSetup.learning_preferences)
    await show_learning_preferences_menu(callback, state, is_new_message=False)
    await callback.answer()

async def show_profile_summary(callback: CallbackQuery, state: FSMContext):
    """Показать сводку профиля для подтверждения"""
    data = await state.get_data()
    
    text = (
        "📋 *Ваш профиль готов!*\n\n"
        f"🎓 *Образование:* {data.get('education_background', 'Не указано')[:50]}...\n\n"
        f"💼 *Опыт работы:* {data.get('work_experience', 'Не указано')[:50]}...\n\n"
        f"🎯 *Интересы:* {', '.join(data.get('interests', []))}\n\n"
        f"🚀 *Цели:* {data.get('career_goals', 'Не указано')[:50]}...\n\n"  
        f"💻 *Программирование:* {data.get('programming_skills', 'Не указано')[:50]}...\n\n"
        f"🤖 *Опыт с ИИ:* {data.get('ai_experience', 'Не указано')[:50]}...\n\n"
        f"📚 *Обучение:* {', '.join(data.get('learning_preferences', []))}\n\n"
        "Сохранить профиль?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сохранить профиль", callback_data="save_profile")],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_profile")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profile")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@profile_router.callback_query(F.data == "save_profile", StateFilter(ProfileSetup.profile_confirmation))
async def save_user_profile(callback: CallbackQuery, state: FSMContext):
    """Сохранение профиля пользователя"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Подготавливаем данные профиля
    profile_data = {
        "user_id": user_id,
        "username": callback.from_user.username,
        "first_name": callback.from_user.first_name,
        "education_background": data.get('education_background'),
        "work_experience": data.get('work_experience'),
        "interests": data.get('interests', []),
        "career_goals": data.get('career_goals'),
        "programming_skills": data.get('programming_skills'),
        "ai_experience": data.get('ai_experience'),
        "learning_preferences": data.get('learning_preferences', []),
        "created_at": str(callback.message.date)
    }
    
    # Сохраняем в JSON файл (временно)
    profile_file = PROFILES_DIR / f"user_{user_id}.json"
    try:
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Профиль пользователя {user_id} сохранен в {profile_file}")
        
        text = (
            "✅ *Профиль сохранен!*\n\n"
            "Теперь я могу дать вам персональные рекомендации по:\n"
            "• Выбору подходящей программы\n"
            "• Планированию изучения курсов\n"
            "• Выборным дисциплинам\n\n"
            "Что хотите сделать дальше?"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Получить рекомендации", callback_data="get_recommendations")],
            [InlineKeyboardButton(text="📚 Изучить программы", callback_data="show_programs")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка сохранения профиля: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при сохранении профиля. Попробуйте еще раз.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
            ])
        )
        await state.clear()
    
    await callback.answer()

@profile_router.callback_query(F.data == "cancel_profile")
async def cancel_profile_setup(callback: CallbackQuery, state: FSMContext):
    """Отмена настройки профиля"""
    await state.clear()
    
    text = "❌ Настройка профиля отменена.\n\nВы можете создать профиль позже для получения персональных рекомендаций."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# Функция для проверки существования профиля
def get_user_profile(user_id: int) -> Dict[str, Any] | None:
    """Получить профиль пользователя"""
    profile_file = PROFILES_DIR / f"user_{user_id}.json"
    
    if not profile_file.exists():
        return None
    
    try:
        with open(profile_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки профиля пользователя {user_id}: {e}")
        return None