/**
 * KanFlow – AI Notes Extraction (board page)
 *
 * Flow:
 *  1. User clicks "Da appunti" → AI modal opens (Step 1: textarea)
 *  2. User pastes notes → clicks "Analizza con AI"
 *  3. POST /api/projects/<id>/extract-tasks → Gemini returns task list
 *  4. Step 2 shows preview cards, all pre-selected
 *  5. User toggles checkboxes → clicks "Importa selezionate"
 *  6. Each selected task is created via normal POST /api/projects/<id>/tasks
 *  7. Board re-renders with newly imported tasks
 */

"use strict";

/* ── DOM refs ────────────────────────────────────────────────────────────── */

const btnAiExtract    = document.getElementById("btn-ai-extract");

const aiModal         = document.getElementById("ai-modal");
const aiModalClose    = document.getElementById("ai-modal-close");
const aiModalCancel   = document.getElementById("ai-modal-cancel");

const aiStepInput     = document.getElementById("ai-step-input");
const aiStepPreview   = document.getElementById("ai-step-preview");
const aiLoading       = document.getElementById("ai-loading");

const aiNotesInput    = document.getElementById("ai-notes-input");
const aiPreviewList   = document.getElementById("ai-preview-list");
const aiPreviewCount  = document.getElementById("ai-preview-count");

const aiFooterStep1   = document.getElementById("ai-footer-step1");
const aiFooterStep2   = document.getElementById("ai-footer-step2");
const aiExtractBtn    = document.getElementById("ai-extract-btn");
const aiBackBtn       = document.getElementById("ai-back-btn");
const aiImportBtn     = document.getElementById("ai-import-btn");

/* ── State ───────────────────────────────────────────────────────────────── */

/** @type {Array<{title:string, description:string, status:string, selected:boolean}>} */
let _extractedTasks = [];

/* ── Step management ─────────────────────────────────────────────────────── */

function showStep(step) {
  aiStepInput.classList.toggle("hidden",   step !== 1);
  aiStepPreview.classList.toggle("hidden", step !== 2);
  aiFooterStep1.classList.toggle("hidden", step !== 1);
  aiFooterStep2.classList.toggle("hidden", step !== 2);
  aiLoading.classList.add("hidden");
}

function showLoading(visible) {
  aiLoading.classList.toggle("hidden", !visible);
}

/* ── Open / close modal ──────────────────────────────────────────────────── */

function openAiModal() {
  _extractedTasks = [];
  aiNotesInput.value = "";
  aiPreviewList.innerHTML = "";
  showStep(1);
  openModal("ai-modal");
  setTimeout(() => aiNotesInput.focus(), 80);
}

function closeAiModal() {
  closeModal("ai-modal");
}

/* ── Render preview cards ────────────────────────────────────────────────── */

function renderPreview(tasks) {
  aiPreviewList.innerHTML = "";

  if (tasks.length === 0) {
    aiPreviewList.innerHTML = `
      <div class="ai-empty-state">
        ✦ Nessuna task trovata nel testo.<br>
        <small>Prova con un testo più strutturato o con bullet point.</small>
      </div>`;
    aiPreviewCount.textContent = "Nessuna task trovata";
    // Disable import button
    aiImportBtn.disabled = true;
    return;
  }

  aiImportBtn.disabled = false;

  // Select-all header
  const selectAllRow = document.createElement("div");
  selectAllRow.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin-bottom:.4rem;";
  selectAllRow.innerHTML = `
    <span style="font-size:.75rem;color:var(--text-3);">Clicca per selezionare/deselezionare</span>
    <label class="ai-select-all">
      <input type="checkbox" id="ai-check-all" checked /> Seleziona tutte
    </label>`;
  aiPreviewList.appendChild(selectAllRow);

  // Task cards
  tasks.forEach((task, idx) => {
    const div = document.createElement("div");
    div.className = "ai-task-preview selected";
    div.dataset.idx = idx;

    const statusClass = `ai-task-preview__status--${task.status.replace("_", "-").replace("in-progress","in_progress")}`;
    const statusLabel = { todo: "TODO", in_progress: "IN PROGRESS", done: "DONE" }[task.status] ?? task.status;

    div.innerHTML = `
      <div class="ai-task-preview__check"></div>
      <div class="ai-task-preview__body">
        <p class="ai-task-preview__title">${escHtml(task.title)}</p>
        ${task.description
          ? `<p class="ai-task-preview__desc">${escHtml(task.description)}</p>`
          : ""}
      </div>
      <span class="ai-task-preview__status ai-task-preview__status--${task.status}">${statusLabel}</span>`;

    div.addEventListener("click", () => togglePreviewCard(div, idx));
    aiPreviewList.appendChild(div);
  });

  updatePreviewCount();

  // Select-all checkbox wiring
  document.getElementById("ai-check-all").addEventListener("change", e => {
    _extractedTasks.forEach(t => t.selected = e.target.checked);
    aiPreviewList.querySelectorAll(".ai-task-preview").forEach(card => {
      card.classList.toggle("selected", e.target.checked);
    });
    updatePreviewCount();
  });
}

function togglePreviewCard(card, idx) {
  _extractedTasks[idx].selected = !_extractedTasks[idx].selected;
  card.classList.toggle("selected", _extractedTasks[idx].selected);
  updatePreviewCount();

  // Sync select-all checkbox state
  const all    = _extractedTasks.length;
  const chosen = _extractedTasks.filter(t => t.selected).length;
  const chkAll = document.getElementById("ai-check-all");
  if (chkAll) {
    chkAll.checked       = chosen === all;
    chkAll.indeterminate = chosen > 0 && chosen < all;
  }
}

function updatePreviewCount() {
  const total   = _extractedTasks.length;
  const chosen  = _extractedTasks.filter(t => t.selected).length;
  aiPreviewCount.textContent = `${total} task trovate · ${chosen} selezionate`;
  aiImportBtn.textContent    = `Importa ${chosen > 0 ? chosen : "selezionate"}`;
  aiImportBtn.disabled       = chosen === 0;
}

/* ── API calls ───────────────────────────────────────────────────────────── */

async function runExtraction() {
  const notes = aiNotesInput.value.trim();
  if (!notes) {
    aiNotesInput.focus();
    return;
  }

  aiExtractBtn.disabled = true;
  showLoading(true);

  try {
    const data = await api(
      `/api/projects/${PROJECT_ID}/extract-tasks`,
      "POST",
      { notes }
    );

    _extractedTasks = (data.tasks || []).map(t => ({ ...t, selected: true }));
    showStep(2);
    renderPreview(_extractedTasks);

  } catch (err) {
    showLoading(false);
    showToast("Errore AI: " + err.message, "error", 5000);
  } finally {
    aiExtractBtn.disabled = false;
  }
}

async function importSelected() {
  const toImport = _extractedTasks.filter(t => t.selected);
  if (toImport.length === 0) return;

  aiImportBtn.disabled = true;
  aiImportBtn.textContent = "Importazione…";

  let created = 0;
  let failed  = 0;

  // Sequential creation to preserve order
  for (const task of toImport) {
    try {
      const created_task = await api(
        `/api/projects/${PROJECT_ID}/tasks`,
        "POST",
        { title: task.title, description: task.description, status: task.status }
      );
      _tasks.push(created_task);
      created++;
    } catch (_) {
      failed++;
    }
  }

  renderBoard();
  closeAiModal();

  if (failed > 0) {
    showToast(`${created} task importate, ${failed} fallite.`, "error");
  } else {
    showToast(`✦ ${created} task importate con successo!`, "success");
  }
}

/* ── Event wiring ────────────────────────────────────────────────────────── */

btnAiExtract.addEventListener("click", openAiModal);
aiModalClose.addEventListener("click", closeAiModal);
aiModalCancel.addEventListener("click", closeAiModal);

aiExtractBtn.addEventListener("click", runExtraction);
aiBackBtn.addEventListener("click",    () => showStep(1));
aiImportBtn.addEventListener("click",  importSelected);

// Ctrl+Enter to extract from notes textarea
aiNotesInput.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    runExtraction();
  }
});
