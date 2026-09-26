"""
API Routes Package for Gistly.
"""

from api.routes.health import router as health_router
from api.routes.meetings import router as meetings_router
from api.routes.chat import router as chat_router
from api.routes.actions import router as actions_router
from api.routes.voice import router as voice_router

__all__ = [
    "health_router",
    "meetings_router",
    "chat_router",
    "actions_router",
    "voice_router",
]
