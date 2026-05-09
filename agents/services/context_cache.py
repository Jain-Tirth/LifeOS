from django.core.cache import cache
from agents.models import UserProfile
from asgiref.sync import sync_to_async
import json
import logging

logger = logging.getLogger(__name__)

class UserContextCache:
    CACHE_TTL = 3600  # 1 hour

    @staticmethod
    def get_cache_key(user_id: int, agent_type: str = None) -> str:
        return f"user_context:{user_id}:{agent_type or 'all'}"

    @classmethod
    async def get_context(cls, user, agent_type=None):
        if not user or not user.is_authenticated:
            return {}

        key = cls.get_cache_key(user.id, agent_type)
        cached = cache.get(key)

        if cached:
            return json.loads(cached)

        # Not in cache, fetch from DB
        profile = await sync_to_async(
            lambda: UserProfile.objects.filter(user=user).first()
        )()

        if profile:
            context = await sync_to_async(
                lambda: profile.get_agent_context(agent_type)
            )()
        else:
            context = {'name': user.get_full_name(), 'timezone': 'Asia/Kolkata'}

        # Cache for 1 hour
        cache.set(key, json.dumps(context), cls.CACHE_TTL)
        return context

    @staticmethod
    def invalidate(user_id: int):
        """Clear cache when profile updated"""
        for agent_type in [None, 'meal_planner_agent', 'productivity_agent', 'wellness_agent', 'study_agent']:
            key = UserContextCache.get_cache_key(user_id, agent_type)
            cache.delete(key)
