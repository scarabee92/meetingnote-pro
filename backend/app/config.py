"""환경 값. .env 는 프로젝트 루트의 것만 읽는다 (backend/ 안의 .env 는 읽지 않음)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

# 코드 기본값 - .env 에 두지 않는다 (배포에서는 Vercel 환경 변수로 덮어씀)
JWT_SECRET = os.getenv("JWT_SECRET", "meetingnote-pro-local-dev-secret-change-in-deploy")
JWT_HOURS = 24
BCRYPT_ROUNDS = 10
CORS_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
TEAM_MAX_MEMBERS = 6
COMMENT_MAX = 500
TRANSCRIBE_TIMEOUT_SEC = 60


def gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "")


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "")


def deployed() -> bool:
    """DATABASE_URL 이 있으면 배포 환경으로 본다."""
    return bool(os.getenv("DATABASE_URL"))


def default_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url
    return f"sqlite:///{(ROOT / 'meetingnote.db').as_posix()}"
