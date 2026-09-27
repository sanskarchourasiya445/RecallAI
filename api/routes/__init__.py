"""
API Routes Package for RecallAI.
"""

from api.routes.health import router as health_router
from api.routes.meetings import router as meetings_router
from api.routes.chat import router as chat_router
from api.routes.actions import router as actions_router
from api.routes.voice import router as voice_router
from api.routes.search import router as search_router
from api.routes.workspace import router as workspace_router
from api.routes.livekit import router as livekit_router

__all__ = [
    "health_router",
    "meetings_router",
    "chat_router",
    "actions_router",
    "voice_router",
    "search_router",
    "workspace_router",
    "livekit_router",
]
