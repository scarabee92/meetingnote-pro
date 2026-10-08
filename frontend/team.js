// team.html - 팀 설정 (스토리보드 F-01 ~ F-08)
// 쓰이는 API: GET·POST·PUT /api/teams · POST /api/teams/join · GET /api/teams/{id}/members
//             PUT /api/teams/{id}/code · GET /api/teams/{id}/activities
document.getElementById("themeSlot").innerHTML = window.THEME_BTN;
window.initTheme();

const $ = (id) => document.getElementById(id);
const COLOR_OF_KIND = { meeting_add: "blue", todo_assign: "orange", todo_done: "green", comment_add: "purple", member_join: "purple" };

let me = null, team = null, MEMBERS = [], ACTS = [];

const msg = (kind, title, body) => {
  $("codeMsg").innerHTML = window.notice(kind, title, body);
  $("codeMsg").classList.remove("hidden");
};

function render() {
  $("members").innerHTML = MEMBERS.map((m) => `
      <li class="rounded-xl bg-page dark:bg-chip border border-line dark:border-edge p-3 flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-white dark:bg-surface border border-line dark:border-edge grid place-items-center text-[13px] font-extrabold">${API.esc(m.name[0] || "")}</div>
        <div class="flex-1 min-w-0">
          <p class="text-[13px] font-bold">${API.esc(m.name)}</p>
          <p class="text-[11px] text-ink-3 dark:text-dim truncate">${API.esc(m.email)}</p>
        </div>
        <div class="text-right shrink-0">
          <span class="px-2 py-0.5 rounded-md text-[10px] font-extrabold ${m.role === "owner" ? window.LABEL.purple : "text-ink-2 dark:text-dim"} bg-white dark:bg-surface">${m.role}</span>
          <p class="mt-1 text-[10px] text-ink-3 dark:text-dim">할 일 ${m.todo_count}</p>
        </div>
      </li>`).join("");
  $("mCap").textContent = MEMBERS.length + " / " + (team ? team.max_members : 6);
  $("acts").innerHTML = ACTS.map((a) => `
      <li class="rounded-xl bg-page dark:bg-chip border border-line dark:border-edge ${window.STRIPE[COLOR_OF_KIND[a.kind]]} px-3.5 py-2.5">
        <p class="text-[13px]"><span class="font-bold">${API.esc(a.actor_name)}</span>  ·  ${API.esc(a.text)}</p>
        <p class="text-[11px] text-ink-3 dark:text-dim mt-0.5">${API.fmtDateTime(a.created_at)}</p>
      </li>`).join("");
}

function setView(hasTeam) {
  $("onboard").classList.toggle("hidden", hasTeam);
  $("info").classList.toggle("hidden", !hasTeam);
  $("members").closest("section").classList.toggle("hidden", !hasTeam);
  $("acts").closest("section").classList.toggle("hidden", !hasTeam);
}

function fillTeam() {
  $("tName").value = team.name;
  $("code").textContent = team.invite_code;
  const owner = team.role === "owner";
  // member 는 읽기만 가능. 권한 등급은 owner / member 둘뿐
  $("tName").readOnly = !owner;
  $("tName").classList.toggle("opacity-60", !owner);
  [$("copyBtn"), $("newCodeBtn"), $("saveName")].forEach((b) => {
    b.classList.toggle("opacity-40", !owner);
    b.classList.toggle("pointer-events-none", !owner);
  });
  // 복사는 읽기이므로 member 도 쓸 수 있게 두지 않고 디자인의 member 화면을 따른다
  $("copyBtn").disabled = !owner; $("newCodeBtn").disabled = !owner; $("saveName").disabled = !owner;
}

async function loadTeam() {
  const teams = await API.get("/api/teams");
  if (!teams.length) { team = null; setView(false); return; }
  team = teams[0];
  setView(true);
  fillTeam();
  MEMBERS = await API.get(`/api/teams/${team.id}/members`);
  try { ACTS = await API.get(`/api/teams/${team.id}/activities`); } catch (e) { ACTS = []; }
  render();
}

async function createTeam() {
  const name = $("newTeamName").value.trim();
  $("joinErr").classList.add("hidden");
  if (!name) { $("joinErr").innerHTML = window.notice("red", "팀 이름을 입력해 주세요"); $("joinErr").classList.remove("hidden"); return; }
  await API.busy($("createBtn"), "만드는 중...", async () => {
    try { await API.post("/api/teams", { name }); await loadTeam(); }
    catch (e) { $("joinErr").innerHTML = window.notice("red", "팀을 만들지 못함", e.msg); $("joinErr").classList.remove("hidden"); }
  });
}

async function joinTeam() {
  const code = $("joinCode").value.trim();
  $("joinErr").classList.add("hidden");
  await API.busy($("joinBtn"), "합류 중...", async () => {
    try { await API.post("/api/teams/join", { invite_code: code }); await loadTeam(); }
    catch (e) {
      const t = e.code === "INVITE_NOT_FOUND" ? ["없는 초대코드", "코드를 다시 확인"]
        : e.code === "TEAM_FULL" ? ["팀 정원이 찼음", "팀당 6명 이내"]
        : ["합류하지 못함", e.msg];
      // 코드가 틀려도 가입 계정은 그대로 유지
      $("joinErr").innerHTML = window.notice("red", t[0], t[1]);
      $("joinErr").classList.remove("hidden");
    }
  });
}

async function saveName() {
  await API.busy($("saveName"), "저장 중...", async () => {
    try {
      team = await API.put(`/api/teams/${team.id}`, { name: $("tName").value });
      fillTeam();
      msg("green", "팀 이름을 저장함");
    } catch (e) { msg("red", e.code === "OWNER_ONLY" ? "owner 만 바꿀 수 있음" : "저장하지 못함", e.msg); }
  });
}

async function copyCode() {
  try { await navigator.clipboard.writeText(team.invite_code); } catch (e) {}
  msg("green", "초대코드를 복사함", "받는 사람은 회원가입 화면의 초대코드 칸에 붙여넣음");
}

async function newCode() {
  const old = team.invite_code;
  await API.busy($("newCodeBtn"), "발급 중...", async () => {
    try {
      const d = await API.put(`/api/teams/${team.id}/code`);
      team.invite_code = d.invite_code;
      fillTeam();
      msg("orange", "초대코드를 다시 발급함", `앞의 코드 ${old} 는 더 쓸 수 없음. 이미 합류한 멤버는 그대로`);
    } catch (e) { msg("red", e.code === "OWNER_ONLY" ? "owner 만 발급할 수 있음" : "발급하지 못함", e.msg); }
  });
}

(async function main() {
  me = await API.guard();
  if (!me) return;
  $("createBtn").onclick = createTeam;
  $("joinBtn").onclick = joinTeam;
  $("saveName").onclick = saveName;
  $("copyBtn").onclick = copyCode;
  $("newCodeBtn").onclick = newCode;
  await loadTeam();
})();
