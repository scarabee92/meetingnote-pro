import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from backend.app import config
from backend.app.errors import CODES
from backend.app.main import create_app
from backend.app.models import TABLES

ROOT = Path(__file__).resolve().parents[1]


def test_테이블_7개(app):
    names = set(inspect(app.state.engine).get_table_names())
    assert set(TABLES) <= names and len(TABLES) == 7


def test_오류코드는_15종():
    assert len(CODES) == 15 and "UNAUTHORIZED" in CODES


def test_토큰_없는_호출은_401_코드와_메시지(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    assert set(r.json()) == {"code", "msg"} and r.json()["code"] in CODES


def test_없는_경로는_NOT_FOUND(client):
    r = client.get("/api/없는경로")
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"


def test_검증_오류는_VALIDATION_ERROR(client):
    r = client.post("/api/auth/login", json={})
    assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"


def test_docs는_로컬에서만(tmp_path):
    url = f"sqlite:///{(tmp_path / 'd.db').as_posix()}"
    local = TestClient(create_app(db_url=url, deployed=False))
    assert local.get("/docs").status_code == 200
    spec = local.get("/openapi.json").json()
    assert "HTTPBearer" in spec["components"]["securitySchemes"]  # Authorize 버튼
    deployed = TestClient(create_app(db_url=url, deployed=True))
    assert deployed.get("/docs").status_code == 404
    assert deployed.get("/openapi.json").status_code == 404


def test_DATABASE_URL이_있으면_배포로_본다(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert config.deployed() is True
    assert config.default_db_url().startswith("postgresql+psycopg://")
    monkeypatch.delenv("DATABASE_URL")
    assert config.deployed() is False and config.default_db_url().startswith("sqlite:///")


def test_backend_안의_env는_읽지_않는다():
    stray = ROOT / "backend" / ".env"
    stray.write_text("GEMINI_MODEL=from-backend-dir\n", encoding="utf-8")
    try:
        env = {k: v for k, v in os.environ.items() if k != "GEMINI_MODEL"}
        out = subprocess.run(
            [sys.executable, "-I", "-c",
             "import sys;sys.path.insert(0,r'%s');from backend.app import config;print(config.gemini_model())" % ROOT],
            capture_output=True, text=True, env=env, cwd=str(ROOT / "backend"),
        )
    finally:
        stray.unlink()
    assert "from-backend-dir" not in out.stdout


def test_키가_응답에_나오지_않는다(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-KEY-VALUE")
    for path in ("/openapi.json", "/api/auth/me", "/login.html"):
        assert "SECRET-KEY-VALUE" not in client.get(path).text


def test_jwt와_cors는_env가_아니라_코드_기본값():
    assert config.JWT_SECRET and config.CORS_ORIGINS
