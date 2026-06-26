import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_debug: bool
    database_url: str
    image_provider: str
    image_api_key: str
    image_api_base_url: str
    image_model: str
    llm_api_key: str
    llm_api_base_url: str
    llm_model: str


def get_settings() -> Settings:
    load_dotenv(override=False)
    return Settings(
        app_name=os.getenv("APP_NAME", "Creative Workshop"),
        app_env=os.getenv("APP_ENV", "development"),
        app_debug=os.getenv("APP_DEBUG", "true").lower() == "true",
        database_url=os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://root:password@127.0.0.1:3306/creative_workshop?charset=utf8mb4",
        ),
        image_provider=os.getenv("IMAGE_PROVIDER", "mock"),
        image_api_key=os.getenv("IMAGE_API_KEY", ""),
        image_api_base_url=os.getenv("IMAGE_API_BASE_URL", ""),
        image_model=os.getenv("IMAGE_MODEL", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_api_base_url=os.getenv("LLM_API_BASE_URL", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
    )
