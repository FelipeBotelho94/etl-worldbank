import os
from dataclasses import dataclass


@dataclass
class Settings:
    api_base_url: str = os.getenv("API_BASE_URL", "http://api.worldbank.org")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME", "etl_db")
    db_user: str = os.getenv("DB_USER", "etl_user")
    db_password: str = os.getenv("DB_PASSWORD", "etl_pass")
    per_page: int = int(os.getenv("PER_PAGE", 90)) 
    max_pages: int = int(os.getenv("MAX_PAGES", 10))


settings = Settings()