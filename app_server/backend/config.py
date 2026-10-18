import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass(frozen=True)
class Settings:
    pg_host: str = os.getenv("POSTGRES_HOST", "localhost")
    pg_port: int = int(os.getenv("POSTGRES_PORT", "5433"))
    pg_db: str = os.getenv("POSTGRES_DB", "quantpulse_db")
    pg_user: str = os.getenv("POSTGRES_USER", "admin")
    pg_password: str = os.getenv("POSTGRES_PASSWORD", "")
    ai_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8100")
    cors_origins: tuple = ("http://localhost:3000",)


settings = Settings()