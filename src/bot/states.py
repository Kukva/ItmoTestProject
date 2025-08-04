from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    """Основные состояния бота"""
    choosing_program = State()
    asking_questions = State()
    comparing_programs = State()

class ProfileSetup(StatesGroup):
    """Состояния для настройки профиля"""
    education_background = State()
    work_experience = State()
    interests = State()
    career_goals = State()
    programming_skills = State()
    ai_experience = State()
    learning_preferences = State()
    profile_confirmation = State()