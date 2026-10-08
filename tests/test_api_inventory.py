"""정의서 7절의 API 26개가 빠짐없이, 더도 덜도 없이 있는지 본다."""

EXPECTED = {
    # Auth 5
    ("POST", "/api/auth/signup"), ("POST", "/api/auth/login"), ("GET", "/api/auth/me"),
    ("PUT", "/api/auth/me"), ("POST", "/api/auth/logout"),
    # Team 6
    ("POST", "/api/teams"), ("GET", "/api/teams"), ("POST", "/api/teams/join"),
    ("GET", "/api/teams/{team_id}/members"), ("PUT", "/api/teams/{team_id}/code"), ("PUT", "/api/teams/{team_id}"),
    # Meeting 6
    ("POST", "/api/teams/{team_id}/meetings"), ("GET", "/api/teams/{team_id}/meetings"),
    ("GET", "/api/meetings/{meeting_id}"), ("PUT", "/api/meetings/{meeting_id}"),
    ("DELETE", "/api/meetings/{meeting_id}"), ("POST", "/api/upload"),
    # Todo 4
    ("GET", "/api/teams/{team_id}/todos"), ("PUT", "/api/todos/{todo_id}"),
    ("GET", "/api/me/todos"), ("DELETE", "/api/todos/{todo_id}"),
    # Comment 3
    ("POST", "/api/meetings/{meeting_id}/comments"), ("GET", "/api/meetings/{meeting_id}/comments"),
    ("DELETE", "/api/comments/{comment_id}"),
    # Activity 2
    ("GET", "/api/teams/{team_id}/activities"), ("GET", "/api/me/activities"),
}


def test_API는_정확히_26개(client):
    spec = client.get("/openapi.json").json()
    found = {(m.upper(), p) for p, ops in spec["paths"].items() for m in ops}
    assert len(EXPECTED) == 26
    assert found == EXPECTED, (sorted(found - EXPECTED), sorted(EXPECTED - found))


def test_모든_경로에_api_접두사(client):
    assert all(p.startswith("/api/") for p in client.get("/openapi.json").json()["paths"])


def test_로그인과_가입을_뺀_모든_API는_토큰이_필요하다(client):
    spec = client.get("/openapi.json").json()
    open_ones = {"/api/auth/signup", "/api/auth/login"}
    for path, ops in spec["paths"].items():
        for method in ops:
            if path in open_ones:
                continue
            url = path.replace("{team_id}", "1").replace("{meeting_id}", "1").replace("{todo_id}", "1").replace("{comment_id}", "1")
            kwargs = {"files": {"file": ("a.wav", b"RIFF")}} if path == "/api/upload" else {"json": {}}
            r = client.request(method.upper(), url, **kwargs)
            assert r.status_code == 401, (method, path, r.status_code)
