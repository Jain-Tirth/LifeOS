import os
from groq import Groq, AsyncGroq
from django.conf import settings

class GroqClientFactory:
    _instance = None
    _async_instance = None

    @classmethod
    def get_client(cls) -> Groq:
        if cls._instance is None:
            api_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY')
            cls._instance = Groq(api_key=api_key)
        return cls._instance

    @classmethod
    def get_async_client(cls) -> AsyncGroq:
        if cls._async_instance is None:
            api_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY')
            cls._async_instance = AsyncGroq(api_key=api_key)
        return cls._async_instance
