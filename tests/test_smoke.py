def test_가입_로그인_보호API_흐름(client, api):
    d = api.signup(email="smoke@x.com", name="스모크")
    assert d["token"] and d["user"]["email"] == "smoke@x.com"
    r = client.post("/api/auth/login", json={"email": "smoke@x.com", "password": "password1"})
    assert r.status_code == 200
    h = {"Authorization": "Bearer " + r.json()["token"]}
    assert client.get("/api/auth/me", headers=h).json()["name"] == "스모크"
