// login.html - 로그인 / 회원가입 (스토리보드 B-01 ~ B-11)
// 쓰이는 API: POST /api/auth/signup · /api/auth/login · /api/teams/join
document.getElementById("themeSlot").innerHTML = window.THEME_BTN;
window.initTheme();

const $ = (id) => document.getElementById(id);
const email = $("email"), pw = $("pw"), uname = $("uname"), invite = $("invite"), submit = $("submit");
let mode = "login";

const reset = () => {
  ["errEmail", "errPw", "errName", "errInvite", "boxErr", "boxOk", "boxExpired"].forEach((i) => $(i).classList.add("hidden"));
  [email, pw, uname, invite].forEach((el) => el.classList.remove("border-red-dot"));
  submit.disabled = false;
};
const err = (id, input, msg) => {
  $(id).textContent = msg;
  $(id).classList.remove("hidden");
  if (input) input.classList.add("border-red-dot");
};
const box = (which, msg) => {
  $(which === "err" ? "boxErrText" : "boxOkText").textContent = msg;
  $(which === "err" ? "boxErr" : "boxOk").classList.remove("hidden");
};

function show(which) {
  mode = which;
  reset();
  const signup = which === "signup";
  $("title").textContent = signup ? "회원가입" : "로그인";
  $("sub").textContent = signup ? "이메일과 비밀번호만 있으면 시작" : "회의록과 할 일을 팀이 함께 관리";
  $("nameWrap").classList.toggle("hidden", !signup);
  $("inviteWrap").classList.toggle("hidden", !signup);
  submit.textContent = signup ? "가입하기" : "로그인";
  $("switch").innerHTML = signup
    ? `이미 계정이 있으신가요? <a href="#" class="font-bold text-blue-text dark:text-blue-dot hover:underline">로그인</a>`
    : `계정이 없으신가요? <a href="#" class="font-bold text-blue-text dark:text-blue-dot hover:underline">회원가입</a>`;
}

$("switch").addEventListener("click", (e) => {
  if (!e.target.closest("a")) return;
  e.preventDefault();
  email.value = ""; pw.value = ""; uname.value = ""; invite.value = "";
  show(mode === "login" ? "signup" : "login");
});

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

async function go() {
  reset();
  const em = email.value.trim(), pass = pw.value;
  // 제출 전에는 오류를 띄우지 않고, 제출하면 화면에서 먼저 거른다
  if (!EMAIL_RE.test(em)) return err("errEmail", email, "이메일 형식이 올바르지 않음");
  if (mode === "signup") {
    if (pass.length < 8) return err("errPw", pw, "비밀번호는 8자 이상");
    if (!uname.value.trim()) return err("errName", uname, "이름을 입력해 주세요");
  } else if (!pass) {
    return err("errPw", pw, "비밀번호를 입력해 주세요");
  }

  await API.busy(submit, "처리 중...", async () => {
    try {
      if (mode === "login") {
        const d = await API.post("/api/auth/login", { email: em, password: pass });
        API.setToken(d.token);
        box("ok", "성공. 이동 중...");
        location.href = d.user.team_id ? "/meetings.html" : "/team.html";
        return;
      }
      const d = await API.post("/api/auth/signup", { email: em, password: pass, name: uname.value.trim() });
      API.setToken(d.token);
      const code = invite.value.trim();
      if (!code) { location.href = "/team.html"; return; } // 비우면 가입 후 팀을 새로 만듦
      try {
        await API.post("/api/teams/join", { invite_code: code });
        location.href = "/meetings.html";
      } catch (e) {
        // 가입은 되고 팀 합류만 실패 - 팀 화면으로 보낸다
        if (e.code !== "INVITE_NOT_FOUND" && e.code !== "TEAM_FULL") throw e;
        err("errInvite", invite, e.code === "TEAM_FULL" ? "정원이 가득 찬 팀" : "없는 초대코드");
        submit.disabled = true;
        setTimeout(() => { location.href = "/team.html"; }, 1500);
      }
    } catch (e) {
      if (e.code === "INVALID_CREDENTIALS") box("err", "이메일 또는 비밀번호가 올바르지 않음");
      else if (e.code === "EMAIL_DUPLICATED") box("err", "이미 가입된 이메일");
      else if (e.code === "EMAIL_INVALID") err("errEmail", email, "이메일 형식이 올바르지 않음");
      else if (e.code === "PASSWORD_TOO_WEAK") err("errPw", pw, "비밀번호는 8자 이상");
      else if (e.code === "NETWORK") box("err", "서버에 연결할 수 없음");
      else box("err", e.msg || "요청을 처리하지 못함");
    }
  });
}

submit.addEventListener("click", go);
[email, pw, uname, invite].forEach((el) => el.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); }));

show("login");
// 세션 만료로 돌아온 경우 (401 TOKEN_EXPIRED)
if (new URLSearchParams(location.search).get("expired")) $("boxExpired").classList.remove("hidden");
// 이미 로그인되어 있으면 바로 들어간다
if (API.token() && !new URLSearchParams(location.search).get("expired")) {
  API.get("/api/auth/me").then((me) => { location.href = me.team_id ? "/meetings.html" : "/team.html"; }).catch(() => {});
}
