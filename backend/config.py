from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str
    MODEL_NAME: str = "openai/gpt-oss-120b"
    MAX_ITERATIONS: int = 10
    TEMPERATURE: float = 0.1

    FIREWORKS_API_KEY: str
    FIREWORKS_MODEL_NAME: str = "accounts/fireworks/models/llama-v3p3-70b-instruct"

    CEREBRAS_API_KEY: str
    CEREBRAS_MODEL_NAME: str = "gpt-oss-120b"

    GOOGLE_API_KEY: str
    GOOGLE_MODEL_NAME: str =  "gemini-3-pro-preview"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()