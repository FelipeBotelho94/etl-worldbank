import os
from dataclasses import dataclass


@dataclass
class Settings:
    # O .rstrip('/') garante que 'v2/' vire 'v2', evitando a barra dupla '//' no extract
    api_base_url: str = os.getenv("API_BASE_URL", "https://api.worldbank.org/v2").rstrip('/')
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME", "etl_db")
    db_user: str = os.getenv("DB_USER", "etl_user")
    db_password: str = os.getenv("DB_PASSWORD", "etl_pass")


settings = Settings()