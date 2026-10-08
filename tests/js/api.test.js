// node --test tests/js  (브라우저 없이 api.js 의 401 처리를 확인)
const test = require("node:test");
const assert = require("node:assert");
const path = require("node:path");

function setup(response) {
  const mem = {};
  globalThis.localStorage = {
    getItem: (k) => (k in mem ? mem[k] : null),
    setItem: (k, v) => { mem[k] = v; },
    removeItem: (k) => { delete mem[k]; },
  };
  globalThis.location = { href: "/meetings.html" };
  globalThis.fetch = async () => ({ ok: response.status < 400, status: response.status, json: async () => response.body });
  const file = path.join(__dirname, "../../frontend/api.js");
  delete require.cache[require.resolve(file)];
  require(file);
  globalThis.API.setToken("tok");
  return globalThis.API;
}

test("세션 만료(TOKEN_EXPIRED)는 토큰을 지우고 로그인 화면으로 보낸다", async () => {
  const API = setup({ status: 401, body: { code: "TOKEN_EXPIRED", msg: "만료" } });
  await assert.rejects(() => API.get("/api/auth/me"));
  assert.strictEqual(API.token(), null);
  assert.match(location.href, /^\/login\.html\?expired=1/);
});

test("로그인 실패(INVALID_CREDENTIALS)는 로그아웃하지 않는다", async () => {
  const API = setup({ status: 401, body: { code: "INVALID_CREDENTIALS", msg: "x" } });
  await assert.rejects(() => API.post("/api/auth/login", {}), (e) => e.code === "INVALID_CREDENTIALS");
  assert.strictEqual(API.token(), "tok");
  assert.strictEqual(location.href, "/meetings.html");
});

test("현재 비밀번호 불일치(UNAUTHORIZED)는 로그아웃하지 않는다", async () => {
  const API = setup({ status: 401, body: { code: "UNAUTHORIZED", msg: "x" } });
  await assert.rejects(() => API.put("/api/auth/me", {}), (e) => e.code === "UNAUTHORIZED");
  assert.strictEqual(API.token(), "tok");
  assert.strictEqual(location.href, "/meetings.html");
});

test("토큰이 없으면 guard 가 로그인 화면으로 보낸다", async () => {
  const API = setup({ status: 200, body: {} });
  API.clearToken();
  assert.strictEqual(await API.guard(), null);
  assert.strictEqual(location.href, "/login.html");
});

test("팀이 없으면 guard(needTeam) 가 팀 화면으로 보낸다", async () => {
  const API = setup({ status: 200, body: { id: 1, team_id: null } });
  assert.strictEqual(await API.guard({ needTeam: true }), null);
  assert.strictEqual(location.href, "/team.html");
});

test("기한 지남은 완료가 아닌 지난 날짜만", () => {
  const API = setup({ status: 200, body: {} });
  assert.strictEqual(API.isLate("2000-01-01", "OPEN"), true);
  assert.strictEqual(API.isLate("2000-01-01", "DONE"), false);
  assert.strictEqual(API.isLate("2999-01-01", "OPEN"), false);
  assert.strictEqual(API.isLate(null, "OPEN"), false);
});
