// 화면 공통 API 호출 모듈 - 모든 화면이 이 하나를 쓴다
// 401 은 오류 코드로 가른다: 세션 만료(TOKEN_EXPIRED)일 때만 토큰을 지우고 로그인 화면으로 보낸다.
// 로그인 실패(INVALID_CREDENTIALS) · 현재 비밀번호 불일치(UNAUTHORIZED)는 그 화면의 오류 문구로 보여 준다.
(function (root) {
  const TOKEN_KEY = "mn_token";
  const store = () => { try { return root.localStorage; } catch (e) { return null; } };

  class ApiError extends Error {
    constructor(status, code, msg) { super(msg); this.status = status; this.code = code; this.msg = msg; }
  }

  const API = {
    ApiError,
    token() { const s = store(); try { return s ? s.getItem(TOKEN_KEY) : null; } catch (e) { return null; } },
    setToken(t) { const s = store(); try { if (s) s.setItem(TOKEN_KEY, t); } catch (e) {} },
    clearToken() { const s = store(); try { if (s) s.removeItem(TOKEN_KEY); } catch (e) {} },
    goLogin(expired) { root.location.href = "/login.html" + (expired ? "?expired=1" : ""); },

    async req(method, path, body) {
      const headers = {};
      const t = API.token();
      if (t) headers["Authorization"] = "Bearer " + t;
      const opt = { method, headers };
      if (typeof FormData !== "undefined" && body instanceof FormData) opt.body = body;
      else if (body !== undefined) { headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
      let res;
      try { res = await root.fetch(path, opt); }
      catch (e) { throw new ApiError(0, "NETWORK", "서버에 연결할 수 없음"); }
      let data = null;
      if (res.status !== 204) { try { data = await res.json(); } catch (e) { data = null; } }
      if (res.ok) return data;
      const err = new ApiError(res.status, (data && data.code) || "UNKNOWN", (data && data.msg) || "요청을 처리하지 못함");
      if (res.status === 401 && err.code === "TOKEN_EXPIRED") { API.clearToken(); API.goLogin(true); }
      throw err;
    },
    get: (p) => API.req("GET", p),
    post: (p, b) => API.req("POST", p, b === undefined ? {} : b),
    put: (p, b) => API.req("PUT", p, b),
    del: (p) => API.req("DELETE", p),

    // 로그인 확인. 토큰이 없으면 로그인 화면으로, needTeam 이면 소속 팀이 없을 때 팀 화면으로
    async guard(opts) {
      opts = opts || {};
      if (!API.token()) { API.goLogin(false); return null; }
      const me = await API.get("/api/auth/me");
      if (opts.needTeam && !me.team_id) { root.location.href = "/team.html"; return null; }
      API.me = me;
      return me;
    },
    async logout() {
      try { await API.post("/api/auth/logout"); } catch (e) {}
      API.clearToken();
      API.goLogin(false);
    },

    // 요청 중에는 버튼을 잠가 두 번 눌리지 않게 한다
    async busy(btn, label, fn) {
      const old = btn ? btn.textContent : "";
      if (btn) { btn.disabled = true; if (label) btn.textContent = label; }
      try { return await fn(); }
      finally { if (btn) { btn.disabled = false; btn.textContent = old; } }
    },

    // ISO 시각(UTC) → 현지 표시
    fmtDateTime(iso) {
      if (!iso) return "";
      const d = new Date(iso);
      if (isNaN(d)) return iso;
      const p = (n) => String(n).padStart(2, "0");
      return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
    },
    fmtDate(iso) {
      if (!iso) return "";
      const d = new Date(iso);
      if (isNaN(d)) return iso;
      return `${d.getMonth() + 1}월 ${d.getDate()}일`;
    },
    // 오늘 날짜(현지) 'YYYY-MM-DD'
    today() {
      const d = new Date(), p = (n) => String(n).padStart(2, "0");
      return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
    },
    // 기한 지남: 완료가 아니고 기한이 오늘보다 앞. 서버는 판정하지 않는다
    isLate(due, status) { return !!due && status !== "DONE" && due < API.today(); },
    esc(s) {
      const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
      return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => map[c]);
    }
  };

  root.API = API;
})(typeof window !== "undefined" ? window : globalThis);
