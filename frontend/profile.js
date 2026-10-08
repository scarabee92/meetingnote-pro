// profile.html - 내 정보 (스토리보드 J-01 ~ J-07)
// 쓰이는 API: GET·PUT /api/auth/me · POST /api/auth/logout · GET /api/me/todos · GET /api/me/activities
document.getElementById("themeSlot").innerHTML = window.THEME_BTN;
window.initTheme(() => render());

const $ = (id) => document.getElementById(id);
const COLOR_OF_KIND = { meeting_add: "blue", todo_assign: "orange", todo_done: "green", comment_add: "purple", member_join: "purple" };
const STATUS = { OPEN: "대기", DOING: "진행", DONE: "완료" };
const STATUS_COLOR = { OPEN: "orange", DOING: "blue", DONE: "green" };

let me = null, TODOS = [], acts = [];

function render() {
  $("todos").innerHTML = TODOS.map((t) => {
    const c = STATUS_COLOR[t.status];
    const late = API.isLate(t.due, t.status);
    return `
      <li class="rounded-xl bg-page dark:bg-chip border border-line dark:border-edge ${late ? window.STRIPE.red : window.STRIPE[c]} px-3.5 py-2.5">
        <p class="text-[13px] font-bold">${API.esc(t.what)}</p>
        <div class="mt-1 flex gap-1.5">
          <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-white dark:bg-surface ${late ? "text-red-text dark:text-red-dot" : "text-ink-2 dark:text-dim"}">${t.due ? API.fmtDate(t.due) : "미정"}</span>
          <span class="px-2 py-0.5 rounded-md text-[10px] font-extrabold ${window.LABEL[c]} bg-white dark:bg-surface">${STATUS[t.status]}</span>
        </div>
      </li>`;
  }).join("");
  $("tCount").textContent = TODOS.length ? TODOS.length + "건" : "";
  $("acts").innerHTML = acts.map((a) => `
      <li class="rounded-xl bg-page dark:bg-chip border border-line dark:border-edge ${window.STRIPE[COLOR_OF_KIND[a.kind]]} px-3.5 py-2.5">
        <p class="text-[13px]">${API.esc(a.text)}</p>
        <p class="text-[11px] text-ink-3 dark:text-dim mt-0.5">${API.fmtDateTime(a.created_at)}  ·  <span class="font-mono">${a.kind}</span></p>
      </li>`).join("");
  $("aCount").textContent = acts.length ? acts.length + "건" : "";
  $("acts").classList.toggle("hidden", acts.length === 0);
  $("aEmpty").classList.toggle("hidden", acts.length > 0);
}

function fillAccount() {
  $("who").textContent = me.name;
  $("who").nextElementSibling.textContent = me.email;
  $("who").parentElement.previousElementSibling.textContent = me.name[0] || "";
  const badge = $("who").parentElement.parentElement.querySelector("span.ml-auto");
  badge.textContent = me.role || "";
  badge.classList.toggle("hidden", !me.role);
  $("name").value = me.name;
}

const msg = (kind, title, body) => {
  $("msg").innerHTML = window.notice(kind, title, body);
  $("msg").classList.remove("hidden");
};
const clearErr = () => {
  ["errName", "errPw", "errCur", "msg"].forEach((i) => $(i).classList.add("hidden"));
  [$("name"), $("pw1"), $("pw2"), $("pwCur")].forEach((el) => el.classList.remove("border-red-dot"));
};
const err = (id, input, text) => {
  $(id).textContent = text;
  $(id).classList.remove("hidden");
  if (input) input.classList.add("border-red-dot");
};

async function save() {
  clearErr();
  const name = $("name").value.trim(), p1 = $("pw1").value, p2 = $("pw2").value, cur = $("pwCur").value;
  if (!name) return err("errName", $("name"), "이름을 입력해 주세요");
  const body = { name };
  if (p1 || p2) {
    // 화면에서 먼저 거른다. 서버로 보내지 않음
    if (p1.length < 8) return err("errPw", $("pw1"), "비밀번호는 8자 이상");
    if (p1 !== p2) return err("errPw", $("pw2"), "두 비밀번호가 다름");
    if (!cur) return err("errCur", $("pwCur"), "현재 비밀번호를 입력해 주세요");
    body.new_password = p1;
    body.current_password = cur;
  }
  await API.busy($("saveBtn"), "저장 중...", async () => {
    try {
      me = await API.put("/api/auth/me", body);
      fillAccount();
      $("pw1").value = ""; $("pw2").value = ""; $("pwCur").value = "";
      msg("green", "저장함", "비밀번호를 바꾸면 기존 토큰은 그대로 유효 (JWT 24h)");
    } catch (e) {
      if (e.code === "UNAUTHORIZED") err("errCur", $("pwCur"), "현재 비밀번호가 올바르지 않음");
      else if (e.code === "PASSWORD_TOO_WEAK") err("errPw", $("pw1"), "비밀번호는 8자 이상");
      else msg("red", "저장하지 못함", e.msg);
    }
  });
}

(async function main() {
  me = await API.guard();
  if (!me) return;
  fillAccount();
  try { TODOS = await API.get("/api/me/todos"); } catch (e) { TODOS = []; }
  try { acts = await API.get("/api/me/activities"); } catch (e) { acts = []; }
  $("saveBtn").onclick = save;
  $("logoutBtn").onclick = () => API.logout();
  render();
})();
