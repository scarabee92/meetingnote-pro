// todos.html - 할 일 칸반 (스토리보드 E-01 ~ E-12)
// 쓰이는 API: GET /api/teams/{id}/todos · GET /api/me/todos · PUT·DELETE /api/todos/{id} · GET /api/teams/{id}/members
document.getElementById("themeSlot").innerHTML = window.THEME_BTN;
window.initTheme(() => render());

const $ = (id) => document.getElementById(id);
const COLS = [
  { key: "OPEN", label: "대기", color: "orange" },
  { key: "DOING", label: "진행", color: "blue" },
  { key: "DONE", label: "완료", color: "green" },
];

let me = null, teamId = null, DATA = [], MEMBERS = [], mine = true, dragId = null, overCol = null;

// ---- 날짜 (기한은 날짜로 저장하고 화면이 오늘과 비교한다) ----
const pad = (n) => String(n).padStart(2, "0");
const ymd = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
function dueCandidates() {
  const t = new Date();
  const fri = addDays(t, ((5 - t.getDay() + 7) % 7));       // 이번 주 금요일 (오늘이 금요일이면 오늘)
  const nextFri = addDays(fri, 7);
  const list = [null, ymd(t), ymd(addDays(t, 1))];
  if (ymd(fri) !== list[1] && ymd(fri) !== list[2]) list.push(ymd(fri));
  list.push(ymd(nextFri));
  return list;
}
function dueLabel(due) {
  if (!due) return "미정";
  const t = new Date();
  if (due === ymd(t)) return "오늘";
  if (due === ymd(addDays(t, 1))) return "내일";
  if (due === ymd(addDays(t, -1))) return "어제";
  return API.fmtDate(due);
}

// ---- 화면 ----
const toast = (kind, title, body) => {
  $("toast").innerHTML = window.notice(kind, title, body);
  $("toast").classList.remove("hidden");
};

const who = (t) => t.assignee_name || "미정";
const late = (t) => API.isLate(t.due, t.status);

const chip = (t) => `
    <article data-id="${t.id}"
      class="card touch-none select-none cursor-grab active:cursor-grabbing rounded-xl bg-white dark:bg-surface border border-line dark:border-edge
             ${late(t) ? window.STRIPE.red : ""} p-3 hover:border-ink dark:hover:border-dim transition
             ${dragId === t.id ? "opacity-40" : ""}">
      <p class="text-[13px] font-bold leading-snug">${API.esc(t.what)}</p>
      <p class="mt-1 text-[11px] text-ink-3 dark:text-dim">${API.esc(t.meeting_title)}</p>
      <div class="mt-2 flex items-center gap-1.5">
        <button type="button" data-act="assign" data-id="${t.id}"
          class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-page dark:bg-chip text-ink-2 dark:text-dim hover:ring-1 hover:ring-ink-3 transition">${API.esc(who(t))}</button>
        <button type="button" data-act="due" data-id="${t.id}"
          class="px-2 py-0.5 rounded-md text-[10px] font-bold ${late(t) ? "text-red-text dark:text-red-dot" : "text-ink-2 dark:text-dim"} bg-page dark:bg-chip hover:ring-1 hover:ring-ink-3 transition">${dueLabel(t.due)}</button>
        <button type="button" data-act="del" data-id="${t.id}"
          class="ml-auto px-2 py-0.5 rounded-md text-[10px] font-bold text-red-text dark:text-red-dot bg-page dark:bg-chip hover:ring-1 hover:ring-red-dot transition">삭제</button>
      </div>
    </article>`;

const visible = () => {
  const f = $("fWho").value;
  return f === "담당자 전체" ? DATA : DATA.filter((t) => who(t) === f); // 담당자 필터는 화면에서 거른다
};

function render() {
  const rows = visible();
  $("board").innerHTML = COLS.map((c) => {
    const items = rows.filter((t) => t.status === c.key);
    const hot = overCol === c.key;
    return `
      <section data-col="${c.key}"
        class="dropzone rounded-2xl bg-white dark:bg-surface border ${hot ? "border-dashed border-2 border-" + c.color + "-dot" : "border-line dark:border-edge"}
               ${window.STRIPE[c.color]} p-4 min-h-[220px] transition">
        <div class="flex items-baseline gap-2 mb-3">
          <h2 class="text-sm font-extrabold ${window.LABEL[c.color]}">${c.label}</h2>
          <span class="text-[11px] text-ink-3 dark:text-dim">${items.length}건</span>
          ${hot ? `<span class="ml-auto text-[10px] font-extrabold ${window.LABEL[c.color]}">여기에 놓기</span>` : ""}
        </div>
        <div class="space-y-2.5">${items.map(chip).join("") ||
          `<p class="text-[12px] text-ink-3 dark:text-dim py-2">없음</p>`}</div>
      </section>`;
  }).join("");
  $("board").classList.toggle("hidden", rows.length === 0);
  $("empty").classList.toggle("hidden", rows.length > 0);
  const done = rows.filter((t) => t.status === "DONE").length;
  $("sum").textContent = rows.length ? `${done} / ${rows.length} 완료` : "";
  $("tabMine").className = "px-3 py-1.5 rounded-lg text-[13px] font-bold transition " +
    (mine ? "bg-white dark:bg-surface shadow-sm" : "text-ink-2 dark:text-dim");
  $("tabAll").className = "px-3 py-1.5 rounded-lg text-[13px] font-bold transition " +
    (!mine ? "bg-white dark:bg-surface shadow-sm" : "text-ink-2 dark:text-dim");
  bindDrag();
  bindBadge();
}

async function load() {
  try { DATA = await API.get(mine ? "/api/me/todos" : `/api/teams/${teamId}/todos`); }
  catch (e) { DATA = []; toast("red", "할 일을 불러오지 못함", e.msg); }
  $("emptyTitle").textContent = "배정된 할 일이 없음";
  $("emptySub").textContent = "회의록을 올리면 할 일이 자동으로 뽑혀 나옴";
  render();
}

// 서버에 한 번만 보낸다. 실패하면 카드가 원래 칸으로 돌아간다
async function save(t, patch, okTitle, okBody) {
  const before = { ...t };
  Object.assign(t, patch.local || {});
  render();
  try {
    const d = await API.put(`/api/todos/${t.id}`, patch.body);
    Object.assign(t, d);
    $("toast").classList.add("hidden");
    if (okTitle) toast("green", okTitle, okBody);
  } catch (e) {
    Object.assign(t, before);
    toast("red", "바꾸지 못함", e.msg);
  }
  render();
}

// 담당자 · 기한 배지는 눌러서 바꾼다. 삭제는 owner 만
function bindBadge() {
  document.querySelectorAll("[data-act]").forEach((el) => {
    el.addEventListener("click", async (e) => {
      e.stopPropagation();
      const t = DATA.find((x) => x.id === +el.dataset.id);
      if (!t) return;
      if (el.dataset.act === "assign") {
        // 멤버를 돌고, 마지막 다음은 미정
        const ids = [...MEMBERS.map((m) => m.id), null];
        const next = ids[(ids.indexOf(t.assignee_id) + 1) % ids.length];
        const name = next === null ? "미정" : MEMBERS.find((m) => m.id === next).name;
        await save(t, { body: { assignee_id: next }, local: { assignee_id: next, assignee_name: next === null ? null : name } },
          "담당자 배정", `「${t.what}」 담당 ${name}`);
      } else if (el.dataset.act === "due") {
        const cand = dueCandidates();
        const i = cand.indexOf(t.due);
        const next = cand[i === -1 ? 1 : (i + 1) % cand.length];
        await save(t, { body: { due: next }, local: { due: next } }, "기한 변경", `「${t.what}」 기한 ${dueLabel(next)}`);
      } else {
        try {
          await API.del(`/api/todos/${t.id}`);
          DATA.splice(DATA.indexOf(t), 1);
          toast("red", "할 일 삭제", `「${t.what}」을 지웠음`);
        } catch (err) {
          toast("red", err.code === "OWNER_ONLY" ? "owner 만 지울 수 있음" : "지우지 못함", err.msg);
        }
        render();
      }
    });
    el.addEventListener("mousedown", (e) => e.stopPropagation());
  });
}

// 끌어 옮기기 - 포인터 이벤트 한 벌로 마우스 · 터치 · 펜을 모두 받는다
//   HTML5 네이티브 드래그(draggable + dragstart)는 터치에서 이벤트가 뜨지 않아 쓰지 않는다
let ghost = null, startX = 0, startY = 0, moved = false;

function colUnder(x, y) {
  const el = document.elementFromPoint(x, y);
  const z = el && el.closest(".dropzone");
  return z ? z.dataset.col : null;
}

function bindDrag() {
  // 카드마다는 누르는 순간만 받는다. 움직임과 놓기는 문서 전체에서 받는다
  // (다시 그리면 카드가 새로 만들어져, 카드에 붙인 리스너는 끌던 중에 사라진다)
  document.querySelectorAll(".card").forEach((el) => {
    el.addEventListener("pointerdown", (e) => {
      if (e.target.closest("[data-act]")) return; // 배지는 누르는 것이지 끄는 것이 아님
      if (e.button !== undefined && e.button !== 0) return;
      dragId = +el.dataset.id;
      startX = e.clientX; startY = e.clientY; moved = false;
    });
  });
}

document.addEventListener("pointermove", (e) => {
  if (dragId === null) return;
  if (!moved) {
    if (Math.abs(e.clientX - startX) < 6 && Math.abs(e.clientY - startY) < 6) return;
    moved = true;
    const el = document.querySelector('.card[data-id="' + dragId + '"]');
    const r = el.getBoundingClientRect();
    ghost = el.cloneNode(true);
    ghost.classList.add("fixed", "pointer-events-none", "z-50", "opacity-80", "shadow-lg");
    ghost.style.width = r.width + "px";
    document.body.appendChild(ghost);
    render();
  }
  e.preventDefault();
  ghost.style.left = (e.clientX - 40) + "px";
  ghost.style.top = (e.clientY - 18) + "px";
  const c = colUnder(e.clientX, e.clientY);
  if (c !== overCol) { overCol = c; render(); }
});

function finishDrag(e) {
  if (dragId === null) return;
  if (ghost) { ghost.remove(); ghost = null; }
  const id = dragId;
  const col = moved && e.type === "pointerup" ? colUnder(e.clientX, e.clientY) : null;
  const wasTap = !moved && e.type === "pointerup";
  const t = DATA.find((x) => x.id === id);
  dragId = null; overCol = null; moved = false;
  if (t && col && t.status !== col) moveTo(t, col); // 놓는 순간 한 번만 호출
  else render();
  // 끌지 않고 눌렀으면 옮길 칸을 고르는 메뉴를 연다 (휴대폰에서 유일한 길)
  if (wasTap && t) openPicker(id);
}
document.addEventListener("pointerup", finishDrag);
document.addEventListener("pointercancel", finishDrag);

function moveTo(t, col) {
  const label = COLS.find((c) => c.key === col).label;
  return save(t, { body: { status: col }, local: { status: col } }, "상태를 옮김", `「${t.what}」를 ${label} 칸으로 옮겼습니다`);
}

// 카드를 누르면 뜨는 상태 선택 메뉴. 끌 수 없는 좁은 화면에서 쓰는 길
function openPicker(id) {
  closePicker();
  const card = document.querySelector('.card[data-id="' + id + '"]');
  const t = DATA.find((x) => x.id === id);
  if (!card || !t) return;
  const box = document.createElement("div");
  box.id = "picker";
  box.className = "mt-2 flex gap-1.5 border-t border-line dark:border-edge pt-2";
  COLS.forEach((c) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = c.label;
    b.className = "flex-1 py-1.5 rounded-lg text-[11px] font-bold transition " +
      (t.status === c.key
        ? "bg-page dark:bg-chip text-ink-3 dark:text-dim"
        : "bg-white dark:bg-surface border border-line dark:border-edge hover:border-ink dark:hover:border-dim " + window.LABEL[c.color]);
    if (t.status !== c.key) b.addEventListener("click", (ev) => { ev.stopPropagation(); moveTo(t, c.key); });
    b.addEventListener("pointerdown", (ev) => ev.stopPropagation());
    box.appendChild(b);
  });
  card.appendChild(box);
}

function closePicker() {
  const p = document.getElementById("picker");
  if (p) p.remove();
}

document.addEventListener("pointerdown", (e) => { if (!e.target.closest(".card")) closePicker(); });

$("tabMine").onclick = () => { mine = true; load(); };
$("tabAll").onclick = () => { mine = false; load(); };
$("fWho").onchange = () => render();

(async function main() {
  me = await API.guard({ needTeam: true });
  if (!me) return;
  teamId = me.team_id;
  MEMBERS = await API.get(`/api/teams/${teamId}/members`);
  $("fWho").innerHTML = ["담당자 전체", ...MEMBERS.map((m) => m.name), "미정"]
    .map((n) => `<option>${API.esc(n)}</option>`).join("");
  await load();
})();
