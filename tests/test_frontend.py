import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCREENS = ["login", "meetings", "detail", "todos", "team", "profile"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node 없음")
def test_api_js_401_처리():
    r = subprocess.run(
        ["node", "--test", str(ROOT / "tests" / "js" / "api.test.js")],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_theme_js는_원본과_같다():
    assert (ROOT / "frontend/theme.js").read_bytes() == (ROOT / "publish/theme.js").read_bytes()


@pytest.mark.parametrize("name", SCREENS)
def test_복사본에_확인용_요소가_없다(name):
    html = (ROOT / f"frontend/{name}.html").read_text(encoding="utf-8")
    assert "stateBar" not in html and 'id="note"' not in html
    js = ROOT / f"frontend/{name}.js"
    if js.exists():
        assert "stateBar" not in js.read_text(encoding="utf-8")


def test_index와_components는_복사하지_않았다():
    assert not (ROOT / "frontend/index.html").exists()
    assert not (ROOT / "frontend/components.html").exists()


@pytest.mark.parametrize("name", SCREENS)
def test_확장자_경로로_화면이_열린다(client, name):
    r = client.get(f"/{name}.html")
    assert r.status_code == 200 and "MeetingNote" in r.text


def test_같은_주소에서_화면과_API(client):
    assert client.get("/login.html").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "/login.html"


def test_허용하지_않은_출처는_CORS_헤더가_없다(client):
    bad = client.options(
        "/api/auth/me",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers
    ok = client.options(
        "/api/auth/me",
        headers={"Origin": "http://localhost:8000", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:8000"
