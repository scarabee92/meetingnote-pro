// meetings.html - 회의록 목록 · 새 회의록 (스토리보드 C-01 ~ C-11)
// 쓰이는 API: GET·POST /api/teams/{id}/meetings · POST /api/upload · GET /api/auth/me · GET /api/teams
document.getElementById("themeSlot").innerHTML = window.THEME_BTN;
window.initTheme(() => render());

const $ = (id) => document.getElementById(id);
const COLORS = ["blue", "green", "orange", "purple", "red"]; // 목록 순서대로 돌려 쓴다
const MAX_BYTES = 25 * 1024 * 1024;

let me = null, teamId = null, DATA = [], filtered = false, saving = false, uploading = false;

const card = (m, i) => {
  const color = COLORS[i % COLORS.length];
  return `
    <article data-id="${m.id}" class="rounded-xl bg-white dark:bg-surface border border-line dark:border-edge
                    ${window.STRIPE[color]} p-4 hover:border-ink dark:hover:border-dim transition cursor-pointer">
      <div class="flex items-start gap-2">
        <h3 class="text-[14px] font-extrabold leading-snug flex-1">${API.esc(m.title)}</h3>
        <span class="px-2 py-0.5 rounded-md text-[10px] font-extrabold ${window.LABEL[color]} bg-page dark:bg-chip shrink-0">
          ${m.todo_done_count}/${m.todo_total_count}</span>
      </div>
      <p class="mt-1 text-[11px] text-ink-3 dark:text-dim">${API.fmtDateTime(m.met_at)}  ·  ${API.esc(m.attendees)}</p>
      <p class="mt-2 text-[12px] text-ink-2 dark:text-dim leading-relaxed line-clamp-2">${API.esc(m.summary)}</p>
      <div class="mt-2.5 flex gap-1.5">
        <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-page dark:bg-chip text-ink-2 dark:text-dim">결정 ${m.decision_count}</span>
        <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-page dark:bg-chip text-ink-2 dark:text-dim">할 일 ${m.todo_total_count}</span>
      </div>
    </article>`;
};

function render() {
  $("list").innerHTML = DATA.map(card).join("");
  $("count").textContent = DATA.length ? DATA.length + "건" : "";
  $("empty").classList.toggle("hidden", DATA.length > 0);
  $("list").classList.toggle("hidden", DATA.length === 0);
  if (!DATA.length) {
    $("emptyTitle").textContent = filtered ? "검색 결과 없음" : "아직 회의록이 없음";
    $("emptySub").textContent = filtered ? "검색어를 지우면 전체 목록으로 돌아감" : "새 회의록 버튼으로 첫 회의를 올려 보기";
  }
}

$("list").addEventListener("click", (e) => {
  const a = e.target.closest("article[data-id]");
  if (a) location.href = "/detail.html?id=" + a.dataset.id;
});

async function load() {
  const p = new URLSearchParams();
  if ($("q").value.trim()) p.set("q", $("q").value.trim());
  if ($("from").value) p.set("from", $("from").value);
  if ($("to").value) p.set("to", $("to").value);
  filtered = [...p.keys()].length > 0;
  try { DATA = await API.get(`/api/teams/${teamId}/meetings` + (filtered ? "?" + p : "")); }
  catch (e) { DATA = []; }
  render();
}

let timer = null;
const reload = () => { clearTimeout(timer); timer = setTimeout(load, 250); };
["q", "from", "to"].forEach((id) => $(id).addEventListener("input", reload));

// ---- 새 회의록 패널 ----
const showErr = (kind, title, body) => {
  $("dropErr").innerHTML = window.notice(kind, title, body);
  $("dropErr").classList.remove("hidden");
};

const resetPanel = () => {
  $("newPanel").classList.add("hidden");
  $("dropErr").classList.add("hidden");
  $("progWrap").classList.add("hidden");
  $("prog").style.width = "0%";
  ["nTitle", "nAt", "nWho", "nBody"].forEach((i) => ($(i).value = ""));
  $("dropTitle").textContent = "녹취 파일을 끌어다 놓기";
  $("dropSub").textContent = "mp3 · wav · 25MB 이하. 또는 아래에 메모를 붙여넣기";
  $("saveBtn").disabled = false;
  $("saveBtn").textContent = "정리하기";
  saving = false;
};

$("newBtn").onclick = () => $("newPanel").classList.remove("hidden");
$("cancelBtn").onclick = resetPanel;

const mb = (n) => (n / 1024 / 1024).toFixed(1) + "MB";

function sendFile(file) {
  if (uploading) return;
  $("dropErr").classList.add("hidden");
  if (file.size > MAX_BYTES) {
    return showErr("red", "25MB 를 넘는 파일", `올린 파일은 ${mb(file.size)}`);
  }
  uploading = true;
  $("dropTitle").textContent = file.name;
  $("dropSub").textContent = `${mb(file.size)}  ·  올리는 중`;
  $("progWrap").classList.remove("hidden");
  $("prog").style.width = "0%";
  $("progText").textContent = "올리는 중  0%";

  const fd = new FormData();
  fd.append("file", file);
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/upload");
  xhr.setRequestHeader("Authorization", "Bearer " + API.token());
  xhr.upload.onprogress = (e) => {
    if (!e.lengthComputable) return;
    const pct = Math.round((e.loaded / e.total) * 100);
    $("prog").style.width = pct + "%";
    $("progText").textContent = pct < 100 ? `올리는 중  ${pct}%` : "받아쓰는 중...";
  };
  xhr.onload = () => {
    uploading = false;
    let d = null;
    try { d = JSON.parse(xhr.responseText); } catch (e) {}
    $("progWrap").classList.add("hidden");
    if (xhr.status === 200 && d) {
      $("nBody").value = d.body;
      $("dropSub").textContent = `${mb(file.size)}  ·  받아쓰기 완료`;
      return;
    }
    $("dropTitle").textContent = "녹취 파일을 끌어다 놓기";
    $("dropSub").textContent = "mp3 · wav · 25MB 이하. 또는 아래에 메모를 붙여넣기";
    const code = d && d.code;
    if (code === "TOKEN_EXPIRED") { API.clearToken(); return API.goLogin(true); }
    if (code === "UNSUPPORTED_MEDIA_TYPE") showErr("red", "mp3 또는 wav 만 올릴 수 있음", `올린 파일: ${file.name}`);
    else if (code === "PAYLOAD_TOO_LARGE") showErr("red", "25MB 를 넘는 파일", `올린 파일은 ${mb(file.size)}`);
    else showErr("red", "받아쓰지 못함", (d && d.msg) || "잠시 뒤 다시 시도");
  };
  xhr.onerror = () => {
    uploading = false;
    $("progWrap").classList.add("hidden");
    showErr("red", "서버에 연결할 수 없음", "");
  };
  xhr.send(fd);
}

// 끌어다 놓기 또는 눌러서 고르기
const picker = document.createElement("input");
picker.type = "file";
picker.accept = ".mp3,.wav,audio/mpeg,audio/wav,audio/x-wav";
picker.className = "hidden";
document.body.appendChild(picker);
picker.addEventListener("change", () => { if (picker.files[0]) sendFile(picker.files[0]); picker.value = ""; });
$("dropZone").classList.add("cursor-pointer");
$("dropZone").addEventListener("click", () => picker.click());

// 끌어다 놓기: 새 회의록 패널 어디에 놓아도 받는다. 창 어디에 놓아도 브라우저가 파일을 열지 않게 막는다
const HOT = ["border-blue-dot", "bg-page", "dark:bg-chip"];
const hot = (on) => HOT.forEach((c) => $("dropZone").classList.toggle(c, on));
const hasFile = (e) => e.dataTransfer && [...(e.dataTransfer.types || [])].includes("Files");
["dragenter", "dragover"].forEach((ev) => window.addEventListener(ev, (e) => {
  if (!hasFile(e)) return;
  e.preventDefault();
  hot(!$("newPanel").classList.contains("hidden") && !!e.target.closest("#newPanel"));
}));
window.addEventListener("dragleave", (e) => { if (!e.relatedTarget) hot(false); });
window.addEventListener("drop", (e) => {
  if (!hasFile(e)) return;
  e.preventDefault();
  hot(false);
  const inPanel = !$("newPanel").classList.contains("hidden") && e.target.closest("#newPanel");
  if (inPanel && e.dataTransfer.files[0]) sendFile(e.dataTransfer.files[0]);
  else if (e.dataTransfer.files[0]) showDropHint(); // 패널이 닫혀 있으면 열어 달라고 알린다
});

function showDropHint() {
  $("newPanel").classList.remove("hidden");
  showErr("orange", "새 회의록 칸에 놓아 주세요", "열어 둔 패널 안에 녹취 파일을 놓으면 받아씀");
}

$("saveBtn").onclick = async () => {
  if (saving) return; // 같은 회의록이 두 번 저장되지 않음
  const title = $("nTitle").value.trim(), at = $("nAt").value, body = $("nBody").value.trim();
  if (!title || !at || !body) return showErr("red", "제목 · 회의 시각 · 본문이 필수");
  saving = true;
  $("dropErr").classList.add("hidden");
  $("saveBtn").disabled = true;
  $("saveBtn").textContent = "정리 중...";
  try {
    await API.post(`/api/teams/${teamId}/meetings`, {
      title, met_at: new Date(at).toISOString(), attendees: $("nWho").value.trim(), body,
    });
    resetPanel();   // 입력칸은 비워지고
    await load();   // 목록 맨 위에 추가
  } catch (e) {
    saving = false;
    $("saveBtn").disabled = false;
    $("saveBtn").textContent = "정리하기";
    showErr("red", "저장하지 못함", e.msg);
  }
};

(async function main() {
  me = await API.guard({ needTeam: true });
  if (!me) return;
  teamId = me.team_id;
  try { const t = await API.get("/api/teams"); if (t[0]) $("teamName").textContent = t[0].name; } catch (e) {}
  await load();
})();
