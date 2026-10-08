import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.main import create_app  # noqa: E402


class FakeGemini:
    """키 없이 도는 가짜 Gemini."""

    def __init__(self):
        self.split_calls = 0
        self.transcribe_calls = 0

    def transcribe(self, data: bytes, mime: str) -> str:
        self.transcribe_calls += 1
        return "오늘은 2차 스프린트 계획 회의입니다. 업로드 용량은 25MB 로 제한하기로 했다. 목록은 김대리가 다음 주 금요일까지 하겠습니다."

    def split(self, body: str) -> dict:
        self.split_calls += 1
        return {
            "summary": "2차 스프린트 계획을 논의했다\n업로드 용량을 25MB 로 정했다",
            "decisions": "업로드 용량은 25MB 로 제한\n목록 화면부터 구현",
            "todos": "목록 화면 구현 | 김대리 | 다음 주 금요일\n인터뷰 진행 | 미정 | 미정",
        }


@pytest.fixture()
def gemini():
    return FakeGemini()


@pytest.fixture()
def app(tmp_path, gemini):
    return create_app(db_url=f"sqlite:///{(tmp_path / 't.db').as_posix()}", deployed=False, gemini=gemini)


@pytest.fixture()
def client(app):
    return TestClient(app)


class Api:
    """가입 · 로그인 · 헤더를 줄여 주는 시험 도구."""

    def __init__(self, client: TestClient):
        self.c = client

    def signup(self, email="a@x.com", password="password1", name="가나다"):
        r = self.c.post("/api/auth/signup", json={"email": email, "password": password, "name": name})
        assert r.status_code == 201, r.text
        return r.json()

    def user(self, email="a@x.com", name="가나다"):
        d = self.signup(email=email, name=name)
        return {"Authorization": "Bearer " + d["token"]}, d["user"]


@pytest.fixture()
def api(client):
    return Api(client)
