/**
 * KanFlow – Kanban Board (board.html)
 * Features:
 *  - Load and render tasks from the API
 *  - Drag-and-drop between and within columns
 *  - Create, edit, delete tasks via modal
 *  - Click card → task preview modal
 *  - Colored label pills on cards with picker in edit modal
 */

"use strict";

/* ── State ───────────────────────────────────────────────────────────────── */

let _tasks           = [];      // all task objects for this board
let _labels          = [];      // all project labels
let _selectedLabelIds = new Set(); // labels selected in the edit/create modal
let _newLabelColor   = "#6C63FF";

let _editingTaskId   = null;
let _previewTaskId   = null;
let _pendingDeleteTaskId = null;
let _taskModalStatus = "todo";

// Drag tracking — used to suppress click→preview after a drag
let _dragEndTime = 0;

/* ── DOM refs ────────────────────────────────────────────────────────────── */

const btnAddTask    = document.getElementById("btn-add-task");

// Task modal
const tmTitle       = document.getElementById("task-modal-title");
const tmTitleInput  = document.getElementById("task-title-input");
const tmDescInput   = document.getElementById("task-desc-input");
const tmSaveBtn     = document.getElementById("task-modal-save");
const tmCancelBtn   = document.getElementById("task-modal-cancel");
const tmCloseBtn    = document.getElementById("task-modal-close");
const tmStatusTabs  = document.querySelectorAll(".status-tab");
const tmLeftActions = document.getElementById("task-modal-left-actions");

// Label picker
const labelChips    = document.getElementById("label-chips");
const labelNewToggle= document.getElementById("label-new-toggle");
const labelNewForm  = document.getElementById("label-new-form");
const labelNameInput= document.getElementById("label-name-input");
const labelCreateBtn= document.getElementById("label-create-btn");
const labelColorDots= document.querySelectorAll(".label-dot");

// Preview modal
const previewModal       = document.getElementById("task-preview-modal");
const previewStatusBadge = document.getElementById("preview-status-badge");
const previewTitle       = document.getElementById("preview-title");
const previewLabels      = document.getElementById("preview-labels");
const previewDesc        = document.getElementById("preview-desc");
const previewMeta        = document.getElementById("preview-meta");
const previewEditBtn     = document.getElementById("preview-edit-btn");
const previewDeleteBtn   = document.getElementById("preview-delete-btn");
const previewClose       = document.getElementById("task-preview-close");

// Confirm delete
const confirmTaskClose  = document.getElementById("confirm-task-close");
const confirmTaskCancel = document.getElementById("confirm-task-cancel");
const confirmTaskDelete = document.getElementById("confirm-task-delete");

/* ── Utilities ───────────────────────────────────────────────────────────── */

function escHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c])
  );
}

function col(status) { return document.getElementById(`col-${status}`); }

function updateCount(status) {
  const el = document.getElementById(`count-${status}`);
  if (el) el.textContent = _tasks.filter(t => t.status === status).length;
}
function updateAllCounts() { ["todo","in_progress","done"].forEach(updateCount); }

/** Build pill HTML for a label object. */
function labelPillHtml(label) {
  const bg   = label.color + "22";   // 13% opacity background
  const fg   = label.color;
  return `<span class="label-pill" style="background:${bg};color:${fg};">${escHtml(label.name)}</span>`;
}

/* ── Task card rendering ─────────────────────────────────────────────────── */

function buildTaskCard(task) {
  const card = document.createElement("div");
  card.className  = "task-card";
  card.dataset.id = task.id;
  card.draggable  = true;

  const labelPills = (task.labels || []).map(labelPillHtml).join("");

  card.innerHTML = `
    <div class="task-card__actions">
      <button class="icon-btn edit-task-btn" title="Modifica" data-id="${task.id}">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </button>
      <button class="icon-btn delete-btn delete-task-btn" title="Elimina" data-id="${task.id}">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6l-1 14H6L5 6"/>
          <path d="M10 11v6M14 11v6"/>
          <path d="M9 6V4h6v2"/>
        </svg>
      </button>
    </div>
    ${labelPills ? `<div class="task-card__labels">${labelPills}</div>` : ""}
    <p class="task-card__title">${escHtml(task.title)}</p>
    ${task.description
      ? `<p class="task-card__desc">${escHtml(task.description)}</p>`
      : ""}`;

  attachDragEvents(card);
  attachCardClickPreview(card);
  return card;
}

function renderBoard() {
  ["todo","in_progress","done"].forEach(status => {
    const container = col(status);
    container.innerHTML = "";
    _tasks
      .filter(t => t.status === status)
      .sort((a, b) => a.position - b.position)
      .forEach(t => container.appendChild(buildTaskCard(t)));
  });
  updateAllCounts();
}

/* ── Task preview ────────────────────────────────────────────────────────── */

const STATUS_LABELS = { todo: "TODO", in_progress: "IN PROGRESS", done: "DONE" };

function openTaskPreview(task) {
  _previewTaskId = task.id;

  // Status badge
  previewStatusBadge.textContent = STATUS_LABELS[task.status] ?? task.status;
  previewStatusBadge.className   = `preview-status-badge status--${task.status}`;

  // Title
  previewTitle.textContent = task.title;

  // Labels
  previewLabels.innerHTML = (task.labels || []).map(labelPillHtml).join("");

  // Description
  previewDesc.textContent = task.description || "";

  // Meta
  const date = task.created_at
    ? new Date(task.created_at).toLocaleDateString("it-IT", { day:"2-digit", month:"long", year:"numeric" })
    : "";
  previewMeta.textContent = date ? `Creata il ${date}` : "";

  openModal("task-preview-modal");
}

function closeTaskPreview() { closeModal("task-preview-modal"); }

/** Attach click-to-preview listener, suppressing clicks that follow a drag. */
function attachCardClickPreview(card) {
  card.addEventListener("click", e => {
    // Ignore if clicked on an action button
    if (e.target.closest(".task-card__actions")) return;
    // Ignore if this click immediately follows a drag (within 300 ms)
    if (Date.now() - _dragEndTime < 300) return;

    const id   = Number(card.dataset.id);
    const task = _tasks.find(t => t.id === id);
    if (task) openTaskPreview(task);
  });
}

// Preview modal buttons
previewEditBtn.addEventListener("click", () => {
  const task = _tasks.find(t => t.id === _previewTaskId);
  if (!task) return;
  closeTaskPreview();
  openTaskModal(task);
});

previewDeleteBtn.addEventListener("click", () => {
  _pendingDeleteTaskId = _previewTaskId;
  closeTaskPreview();
  openModal("confirm-task-modal");
});

previewClose.addEventListener("click", closeTaskPreview);

/* ── Label picker ────────────────────────────────────────────────────────── */

async function loadLabels() {
  try {
    _labels = await api(`/api/projects/${PROJECT_ID}/labels`);
  } catch (_) { _labels = []; }
}

function renderLabelPicker(selectedIds = []) {
  _selectedLabelIds = new Set(selectedIds.map(Number));
  labelChips.innerHTML = "";

  if (_labels.length === 0) {
    labelChips.innerHTML = `<span class="label-chip__empty">Nessuna etichetta — creane una qui sotto.</span>`;
    return;
  }

  _labels.forEach(label => {
    const chip = document.createElement("span");
    chip.className = `label-chip${_selectedLabelIds.has(label.id) ? " selected" : ""}`;

    const bg = label.color + "22";
    chip.style.background = bg;
    chip.style.color      = label.color;
    chip.dataset.id       = label.id;

    chip.innerHTML = `
      <span class="label-chip__check">✓</span>
      ${escHtml(label.name)}
      <button class="label-chip__del" data-label-id="${label.id}" title="Elimina etichetta">✕</button>`;

    // Toggle selection on chip click (but not on delete button)
    chip.addEventListener("click", e => {
      if (e.target.closest(".label-chip__del")) return;
      if (_selectedLabelIds.has(label.id)) {
        _selectedLabelIds.delete(label.id);
        chip.classList.remove("selected");
      } else {
        _selectedLabelIds.add(label.id);
        chip.classList.add("selected");
      }
    });

    // Delete label on ✕ button
    chip.querySelector(".label-chip__del").addEventListener("click", async e => {
      e.stopPropagation();
      try {
        await api(`/api/labels/${label.id}`, "DELETE");
        _labels = _labels.filter(l => l.id !== label.id);
        _selectedLabelIds.delete(label.id);
        // Remove label from all local tasks
        _tasks.forEach(t => { t.labels = (t.labels || []).filter(l => l.id !== label.id); });
        renderBoard();
        renderLabelPicker([..._selectedLabelIds]);
      } catch (err) { showToast(err.message, "error"); }
    });

    labelChips.appendChild(chip);
  });
}

// New label form toggle
labelNewToggle.addEventListener("click", () => {
  labelNewForm.classList.toggle("hidden");
  if (!labelNewForm.classList.contains("hidden")) {
    labelNameInput.value = "";
    labelNameInput.focus();
  }
});

// Color dot picker for new label
labelColorDots.forEach(dot => {
  dot.addEventListener("click", () => {
    labelColorDots.forEach(d => d.classList.remove("active"));
    dot.classList.add("active");
    _newLabelColor = dot.dataset.color;
  });
});

// Create label button
labelCreateBtn.addEventListener("click", async () => {
  const name = labelNameInput.value.trim();
  if (!name) { labelNameInput.focus(); return; }
  try {
    const created = await api(`/api/projects/${PROJECT_ID}/labels`, "POST", {
      name, color: _newLabelColor
    });
    _labels.push(created);
    _selectedLabelIds.add(created.id);
    labelNameInput.value = "";
    labelNewForm.classList.add("hidden");
    renderLabelPicker([..._selectedLabelIds]);
    showToast(`Etichetta "${created.name}" creata ✓`);
  } catch (err) { showToast(err.message, "error"); }
});

labelNameInput.addEventListener("keydown", e => { if (e.key === "Enter") labelCreateBtn.click(); });

/* ── Task modal ──────────────────────────────────────────────────────────── */

function setModalStatus(status) {
  _taskModalStatus = status;
  tmStatusTabs.forEach(tab => tab.classList.toggle("active", tab.dataset.status === status));
}

function openTaskModal(task = null, defaultStatus = "todo") {
  _editingTaskId = task ? task.id : null;

  tmTitle.textContent   = task ? "Modifica Task" : "Nuova Task";
  tmSaveBtn.textContent = task ? "Salva Modifiche" : "Crea Task";
  tmTitleInput.value    = task ? task.title             : "";
  tmDescInput.value     = task ? (task.description || "") : "";

  setModalStatus(task ? task.status : defaultStatus);

  // Label picker
  renderLabelPicker(task ? (task.labels || []).map(l => l.id) : []);

  // Delete button in edit mode
  tmLeftActions.innerHTML = task
    ? `<button class="btn btn--danger btn--sm" id="tm-delete-btn">Elimina task</button>`
    : "";
  if (task) {
    document.getElementById("tm-delete-btn").addEventListener("click", () => {
      closeModal("task-modal");
      _pendingDeleteTaskId = task.id;
      openModal("confirm-task-modal");
    });
  }

  labelNewForm.classList.add("hidden");
  openModal("task-modal");
  tmTitleInput.focus();
  tmTitleInput.select();
}

function closeTaskModal() { closeModal("task-modal"); }

/* ── CRUD operations ─────────────────────────────────────────────────────── */

async function loadTasks() {
  try {
    _tasks = await api(`/api/projects/${PROJECT_ID}/tasks`);
    renderBoard();
  } catch (err) {
    showToast("Errore caricamento task: " + err.message, "error");
  }
}

async function saveTask() {
  const title = tmTitleInput.value.trim();
  if (!title) { tmTitleInput.focus(); return; }

  tmSaveBtn.disabled = true;
  try {
    let task;
    if (_editingTaskId) {
      task = await api(`/api/tasks/${_editingTaskId}`, "PUT", {
        title,
        description: tmDescInput.value.trim(),
        status: _taskModalStatus,
      });
      const idx = _tasks.findIndex(t => t.id === task.id);
      if (idx !== -1) _tasks[idx] = task;
      showToast("Task aggiornata ✓");
    } else {
      task = await api(`/api/projects/${PROJECT_ID}/tasks`, "POST", {
        title,
        description: tmDescInput.value.trim(),
        status: _taskModalStatus,
      });
      _tasks.push(task);
      showToast("Task creata ✓");
    }

    // Save labels (separate call)
    const labelIds = [..._selectedLabelIds];
    const updated  = await api(`/api/tasks/${task.id}/labels`, "PUT", { label_ids: labelIds });
    const finalIdx = _tasks.findIndex(t => t.id === updated.id);
    if (finalIdx !== -1) _tasks[finalIdx] = updated;

    renderBoard();
    closeTaskModal();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    tmSaveBtn.disabled = false;
  }
}

async function deleteTask(id) {
  try {
    await api(`/api/tasks/${id}`, "DELETE");
    _tasks = _tasks.filter(t => t.id !== id);
    renderBoard();
    showToast("Task eliminata");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function moveTask(taskId, newStatus) {
  try {
    const updated = await api(`/api/tasks/${taskId}`, "PUT", { status: newStatus });
    const idx = _tasks.findIndex(t => t.id === updated.id);
    if (idx !== -1) _tasks[idx] = updated;
    updateAllCounts();
  } catch (err) {
    showToast("Spostamento fallito: " + err.message, "error");
    renderBoard();
  }
}

async function reorderColumn(status) {
  const zone     = col(status);
  const domOrder = [...zone.querySelectorAll(".task-card")].map(c => Number(c.dataset.id));
  domOrder.forEach((id, pos) => {
    const t = _tasks.find(t => t.id === id);
    if (t) t.position = pos;
  });
  try {
    await api(`/api/projects/${PROJECT_ID}/reorder`, "POST", { status, order: domOrder });
  } catch (err) {
    showToast("Riordino fallito: " + err.message, "error");
    renderBoard();
  }
}

/* ── Drag-and-drop (HTML5) ───────────────────────────────────────────────── */

let _placeholder = null;

function attachDragEvents(card) {
  card.addEventListener("dragstart", onDragStart);
  card.addEventListener("dragend",   onDragEnd);
}

function onDragStart(e) {
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", e.currentTarget.dataset.id);
  setTimeout(() => e.currentTarget.classList.add("dragging"), 0);
}

function onDragEnd(e) {
  _dragEndTime = Date.now();   // suppress the upcoming click event
  e.currentTarget.classList.remove("dragging");
  removePlaceholder();
  document.querySelectorAll(".kanban-col").forEach(c => c.classList.remove("drag-over"));
}

function removePlaceholder() {
  if (_placeholder && _placeholder.parentNode) _placeholder.parentNode.removeChild(_placeholder);
  _placeholder = null;
}

function createPlaceholder() {
  const el = document.createElement("div");
  el.className = "drop-placeholder";
  return el;
}

document.querySelectorAll(".kanban-col__cards").forEach(zone => {
  zone.addEventListener("dragover", e => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";

    document.querySelectorAll(".kanban-col").forEach(c => c.classList.remove("drag-over"));
    zone.closest(".kanban-col").classList.add("drag-over");

    if (!_placeholder) _placeholder = createPlaceholder();

    const afterEl = getDragAfterElement(zone, e.clientY);
    if (afterEl) zone.insertBefore(_placeholder, afterEl);
    else         zone.appendChild(_placeholder);
  });

  zone.addEventListener("dragleave", e => {
    if (!zone.contains(e.relatedTarget)) {
      zone.closest(".kanban-col").classList.remove("drag-over");
      removePlaceholder();
    }
  });

  zone.addEventListener("drop", async e => {
    e.preventDefault();
    const newStatus = zone.dataset.status;
    const taskId    = Number(e.dataTransfer.getData("text/plain"));

    const placeholderIdx = _placeholder ? [...zone.children].indexOf(_placeholder) : -1;

    removePlaceholder();
    document.querySelectorAll(".kanban-col").forEach(c => c.classList.remove("drag-over"));

    if (!taskId) return;
    const task = _tasks.find(t => t.id === taskId);
    if (!task) return;

    const isSameColumn = task.status === newStatus;

    if (!isSameColumn) {
      task.status = newStatus;
      renderBoard();
      await moveTask(taskId, newStatus);
      if (placeholderIdx !== -1) {
        const cardEl  = zone.querySelector(`[data-id="${taskId}"]`);
        const sibling = zone.children[placeholderIdx];
        if (cardEl && sibling && cardEl !== sibling) zone.insertBefore(cardEl, sibling);
        else if (cardEl && !sibling) zone.appendChild(cardEl);
        await reorderColumn(newStatus);
      }
    } else {
      const cardEl = zone.querySelector(`[data-id="${taskId}"]`);
      if (cardEl && placeholderIdx !== -1) {
        const sibling = zone.children[placeholderIdx];
        if (sibling && sibling !== cardEl) zone.insertBefore(cardEl, sibling);
        else if (!sibling) zone.appendChild(cardEl);
      }
      await reorderColumn(newStatus);
    }
  });
});

function getDragAfterElement(container, y) {
  const draggable = [...container.querySelectorAll(".task-card:not(.dragging)")];
  return draggable.reduce((closest, child) => {
    const box    = child.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > closest.offset) return { offset, element: child };
    return closest;
  }, { offset: Number.NEGATIVE_INFINITY }).element;
}

/* ── Event wiring ────────────────────────────────────────────────────────── */

btnAddTask.addEventListener("click", () => openTaskModal(null, "todo"));

document.querySelectorAll(".col-add-btn").forEach(btn => {
  btn.addEventListener("click", () => openTaskModal(null, btn.dataset.status));
});

tmStatusTabs.forEach(tab => tab.addEventListener("click", () => setModalStatus(tab.dataset.status)));

tmSaveBtn.addEventListener("click", saveTask);
tmCancelBtn.addEventListener("click", closeTaskModal);
tmCloseBtn.addEventListener("click",  closeTaskModal);
tmTitleInput.addEventListener("keydown", e => { if (e.key === "Enter") saveTask(); });

// Edit / delete via action buttons (delegation)
document.getElementById("kanban-board").addEventListener("click", e => {
  const editBtn   = e.target.closest(".edit-task-btn");
  const deleteBtn = e.target.closest(".delete-task-btn");

  if (editBtn) {
    const task = _tasks.find(t => t.id === Number(editBtn.dataset.id));
    if (task) { e.stopPropagation(); openTaskModal(task); }
  }

  if (deleteBtn) {
    e.stopPropagation();
    _pendingDeleteTaskId = Number(deleteBtn.dataset.id);
    openModal("confirm-task-modal");
  }
});

confirmTaskDelete.addEventListener("click", async () => {
  if (!_pendingDeleteTaskId) return;
  closeModal("confirm-task-modal");
  await deleteTask(_pendingDeleteTaskId);
  _pendingDeleteTaskId = null;
});
confirmTaskCancel.addEventListener("click", () => closeModal("confirm-task-modal"));
confirmTaskClose.addEventListener("click",  () => closeModal("confirm-task-modal"));

/* ── Init ─────────────────────────────────────────────────────────────────── */

(async () => {
  await loadLabels();
  await loadTasks();
})();
