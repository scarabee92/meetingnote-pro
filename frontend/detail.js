// detail.html - 회의록 상세 (스토리보드 D-01 ~ D-13)
// 쓰이는 API: GET·PUT·DELETE /api/meetings/{id} · PUT /api/todos/{id} · GET /api/teams/{id}/members
//             POST·GET /api/meetings/{id}/comments · DELETE /api/comments/{id}
document.getElementById("themeSlot").innerHTML = window.THEME_BTN;
window.initTheme(() => renderTodos());

const $ = (id) => document.getElementById(id);
const STATUS = {
  OPEN: { label: "대기", color: "orange" },
  DOING: { label: "진행", color: "blue" },
  DONE: { label: "완료", color: "green" },
};
const meetingId = new URLSearchParams(location.search).get("id");
const EDIT_RING = ["ring-2", "ring-blue-dot/25", "rounded-lg", "px-2"];

let me = null, M = null, TODOS = [], MEMBERS = [], CM = [], editing = false;

// ---- 할 일 ----
const pad = (n) => String(n).padStart(2, "0");
function dueLabel(due) {
  if (!due) return "미정";
  const t = new Date(), ymd = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  if (due === ymd(t)) return "오늘";
  const tm = new Date(t); tm.setDate(t.getDate() + 1);
  if (due === ymd(tm)) return "내일";
  return API.fmtDate(due);
}

const todoRow = (t, i) => {
  const st = STATUS[t.status];
  const late = API.isLate(t.due, t.status);
  const opts = [{ id: "", name: "미정" }, ...MEMBERS]
    .map((m) => `<option value="${m.id}" ${String(t.assignee_id || "") === String(m.id) ? "selected" : ""}>${API.esc(m.name)}</option>`).join("");
  return `
    <li class="rounded-xl bg-page dark:bg-chip border border-line dark:border-edge p-3">
      <p class="text-[13px] font-bold leading-snug">${API.esc(t.what)}</p>
      <div class="mt-2 flex flex-wrap items-center gap-1.5">
        <select data-i="${i}" class="assign h-7 px-2 rounded-md bg-white dark:bg-surface border border-line dark:border-edge text-[11px] font-bold focus:outline-none focus:border-blue-dot transition">${opts}</select>
        <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-white dark:bg-surface ${late ? "text-red-text dark:text-red-dot" : "text-ink-2 dark:text-dim"}">${dueLabel(t.due)}</span>
        <span class="px-2 py-0.5 rounded-md text-[10px] font-extrabold ${window.LABEL[st.color]} bg-white dark:bg-surface ml-auto">${st.label}</span>
      </div>
    </li>`;
};

function renderTodos() {
  if (!TODOS.length) {
    $("todos").innerHTML = `<li class="text-[12px] text-ink-3 dark:text-dim">담당자와 기한이 드러난 항목 없음</li>`;
    return;
  }
  $("todos").innerHTML = TODOS.map(todoRow).join("");
  document.querySelectorAll("select.assign").forEach((sel) => {
    sel.onchange = async () => {
      const t = TODOS[+sel.dataset.i];
      if (!t) return;
      const before = t.assignee_id;
      try {
        const d = await API.put(`/api/todos/${t.id}`, { assignee_id: sel.value ? +sel.value : null });
        Object.assign(t, d);
      } catch (e) {
        t.assignee_id = before; // 실패하면 원래 값으로
        alert(e.msg);
      }
      renderTodos();
    };
  });
}

// ---- 회의록 ----
function renderMeeting() {
  $("title").value = M.title;
  $("at").textContent = API.fmtDateTime(M.met_at);
  $("who").textContent = M.attendees;
  $("summary").textContent = M.summary;
  const dec = M.decisions.split("\n").map((s) => s.trim()).filter(Boolean);
  $("decisions").innerHTML = dec.length
    ? dec.map((d, i) => `<li class="flex gap-2"><span class="text-green-text dark:text-green-dot font-bold shrink-0">${i + 1}</span><span>${API.esc(d)}</span></li>`).join("")
    : `<li class="text-[12px] text-ink-3 dark:text-dim">합의가 끝난 항목 없음  -  논의만 하고 정하지 않은 것은 넣지 않음</li>`;
  $("body").textContent = M.body;
  const ok = M.can_edit; // 올린 사람과 owner 만 고치고 지움
  [$("editBtn"), $("delBtn")].forEach((b) => {
    b.disabled = !ok;
    b.classList.toggle("opacity-40", !ok);
    b.classList.toggle("pointer-events-none", !ok);
  });
}

function setEditing(on) {
  editing = on;
  $("title").readOnly = !on;
  [$("title"), $("at"), $("who"), $("body")].forEach((el) => EDIT_RING.forEach((c) => el.classList.toggle(c, on)));
  [$("at"), $("who"), $("body")].forEach((el) => (el.contentEditable = on ? "true" : "false"));
  $("editBtn").textContent = on ? "저장" : "수정";
  if (on) { $("body").classList.remove("hidden"); $("bodyState").textContent = "접기"; $("title").focus(); }
}

async function saveEdit() {
  const at = $("at").textContent.trim();
  const d = new Date(at.replace(" ", "T"));
  if (isNaN(d)) return alert("회의 시각을 YYYY-MM-DD HH:MM 으로 적어 주세요");
  if (!$("title").value.trim()) return alert("제목을 입력해 주세요");
  await API.busy($("editBtn"), "저장 중...", async () => {
    try {
      await API.put(`/api/meetings/${M.id}`, {
        title: $("title").value, met_at: d.toISOString(),
        attendees: $("who").textContent.trim(), body: $("body").textContent,
      });
      M = await API.get(`/api/meetings/${M.id}`); // 받아쓰기와 세 항목은 그대로
      renderMeeting();
      setEditing(false);
    } catch (e) { alert(e.msg); }
  });
}

$("editBtn").onclick = () => (editing ? saveEdit() : setEditing(true));
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && editing) { renderMeeting(); setEditing(false); }
});
$("bodyToggle").onclick = () => {
  const hid = $("body").classList.toggle("hidden");
  $("bodyState").textContent = hid ? "펼치기" : "접기";
};

$("delBtn").onclick = () => {
  $("delText").textContent = `딸린 할 일 ${TODOS.length}건도 함께 사라짐. 되돌릴 수 없음`;
  $("delConfirm").classList.remove("hidden");
};
$("delNo").onclick = () => $("delConfirm").classList.add("hidden");
$("delYes").onclick = async () => {
  await API.busy($("delYes"), "삭제 중...", async () => {
    try { await API.del(`/api/meetings/${M.id}`); location.href = "/meetings.html"; }
    catch (e) { alert(e.msg); }
  });
};

// ---- 댓글 ----
function renderComments() {
  $("comments").innerHTML = CM.map((c) => `
      <li class="rounded-xl bg-page dark:bg-chip border border-line dark:border-edge px-3.5 py-2.5">
        <p class="text-[13px]"><span class="font-bold">${API.esc(c.user_name)}</span>  ${API.esc(c.content)}</p>
        <p class="text-[11px] text-ink-3 dark:text-dim mt-0.5">${API.fmtDateTime(c.created_at)}
          ${c.can_delete ? `<button type="button" data-del-c="${c.id}" class="ml-2 text-red-text dark:text-red-dot font-bold">삭제</button>` : ""}</p>
      </li>`).join("");
  $("cCount").textContent = CM.length ? CM.length + "건" : "";
  $("comments").classList.toggle("hidden", CM.length === 0);
  $("cEmpty").classList.toggle("hidden", CM.length > 0);
  document.querySelectorAll("[data-del-c]").forEach((b) => {
    b.onclick = async () => {
      try { await API.del(`/api/comments/${b.dataset.delC}`); CM = CM.filter((x) => x.id !== +b.dataset.delC); }
      catch (e) { alert(e.msg); }
      renderComments();
    };
  });
}

$("cInput").maxLength = 500;
const addComment = async () => {
  const text = $("cInput").value.trim();
  if (!text) return;
  await API.busy($("cBtn"), "등록 중...", async () => {
    try {
      CM.push(await API.post(`/api/meetings/${M.id}/comments`, { content: text })); // 목록 맨 아래에 붙음
      $("cInput").value = ""; // 입력칸을 비움
      renderComments();
    } catch (e) { alert(e.msg); }
  });
};
$("cBtn").onclick = addComment;
$("cInput").addEventListener("keydown", (e) => { if (e.key === "Enter") addComment(); });

(async function main() {
  me = await API.guard({ needTeam: true });
  if (!me) return;
  try {
    M = await API.get(`/api/meetings/${meetingId}`);
  } catch (e) {
    // 없는 회의록: 404 MEETING_NOT_FOUND - 목록으로 돌려보냄
    $("title").value = ""; $("summary").textContent = "없는 회의록"; $("decisions").innerHTML = ""; $("todos").innerHTML = "";
    setTimeout(() => { location.href = "/meetings.html"; }, 1500);
    return;
  }
  TODOS = M.todos;
  try { MEMBERS = await API.get(`/api/teams/${M.team_id}/members`); } catch (e) { MEMBERS = []; }
  renderMeeting();
  renderTodos();
  try { CM = await API.get(`/api/meetings/${M.id}/comments`); } catch (e) { CM = []; }
  renderComments();
})();
