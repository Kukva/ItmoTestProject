from .basic import basic_router
from .profile import profile_router, get_user_profile
from .programs import programs_router
from .text import text_router

__all__ = [
    'basic_router',
    'profile_router', 
    'programs_router',
    'text_router',
    'get_user_profile'
]