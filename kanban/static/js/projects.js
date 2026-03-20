/**
 * KanFlow – Projects page (index.html)
 * Handles: create, rename, delete projects.
 */

"use strict";

/* ── State ───────────────────────────────────────────────────────────────── */

let _editingProjectId = null;   // null = creating new, number = editing
let _pendingDeleteId  = null;
let _selectedColor   = "#6C63FF";

/* ── DOM refs ────────────────────────────────────────────────────────────── */

const grid            = document.getElementById("projects-grid");
const btnNewProject   = document.getElementById("btn-new-project");

// Project modal
const projectModal    = document.getElementById("project-modal");
const pmTitle         = document.getElementById("project-modal-title");
const pmNameInput     = document.getElementById("project-name-input");
const pmSaveBtn       = document.getElementById("project-modal-save");
const pmCancelBtn     = document.getElementById("project-modal-cancel");
const pmCloseBtn      = document.getElementById("project-modal-close");
const colorSwatches   = document.querySelectorAll(".swatch");

// Confirm-delete modal
const confirmModal    = document.getElementById("confirm-modal");
const confirmMsg      = document.getElementById("confirm-modal-msg");

/* ── Progress helpers ────────────────────────────────────────────────────── */

/**
 * Apply the is-complete CSS class (green glow) when pct === 100.
 * Call on every card after render or after a task status changes.
 */
function applyProgressState(card) {
  const bar   = card.querySelector(".progress-bar");
  const label = card.querySelector(".progress-label");
  if (!bar || !label) return;
  const pct = parseFloat(bar.style.width) || 0;
  bar.classList.toggle("is-complete",   pct === 100);
  label.classList.toggle("is-complete", pct === 100);
}

/**
 * Refresh progress data for a single card from the API
 * (called when returning from a board page, or after any task change).
 * @param {HTMLElement} card
 */
async function refreshCardProgress(card) {
  const id = card.dataset.id;
  try {
    const p = await api(`/api/projects/${id}`);
    updateCardProgress(card, p.task_count, p.done_count, p.completion_pct, p.in_progress_count, p.in_progress_pct);
  } catch (_) { /* silent */ }
}

/**
 * Update the visible progress values on an existing card element.
 */
function updateCardProgress(card, total, done, pct, wip, wipPct) {
  const meta  = card.querySelector(".project-card__meta");
  const bar   = card.querySelector(".progress-bar:not(.progress-bar--wip)");
  const wipBar= card.querySelector(".progress-bar--wip");
  const label = card.querySelector(".progress-label");
  const wrap  = card.querySelector(".progress-wrap");

  const metaWip  = wip   ? ` · ${wip} in progress` : "";
  const labelWip = wipPct ? ` · ${wipPct}% in corso` : "";

  if (meta)   meta.innerHTML = `${total} task${total !== 1 ? "s" : ""} &middot; ${done} done${metaWip}`;
  if (bar)    bar.style.width = pct + "%";
  if (wipBar) { wipBar.style.width = wipPct + "%"; wipBar.style.left = pct + "%"; }
  if (wrap)   wrap.setAttribute("title", `${pct}% done${wipPct ? `, ${wipPct}% in progress` : ""}`);
  if (label)  label.textContent = `${pct}% completato${labelWip}`;

  applyProgressState(card);
}

/* Refresh all visible cards once the DOM is ready (handles back-navigation) */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".project-card").forEach(card => {
    applyProgressState(card);       // decorate server-rendered state
    refreshCardProgress(card);      // pull fresh numbers from API
  });
});
const confirmDelete   = document.getElementById("confirm-delete");
const confirmCancel   = document.getElementById("confirm-cancel");
const confirmClose    = document.getElementById("confirm-modal-close");

/* ── Project modal helpers ───────────────────────────────────────────────── */

function openProjectModal(id = null, name = "", color = "#6C63FF") {
  _editingProjectId = id;
  _selectedColor    = color;

  pmTitle.textContent    = id ? "Rename Project" : "New Project";
  pmSaveBtn.textContent  = id ? "Save Changes"  : "Create Project";
  pmNameInput.value      = name;

  // sync colour swatches
  colorSwatches.forEach(s => {
    s.classList.toggle("active", s.dataset.color === color);
  });

  openModal("project-modal");
  pmNameInput.select();
}

function closeProjectModal() { closeModal("project-modal"); }

/* ── Build a project card DOM element ────────────────────────────────────── */

function buildProjectCard(p) {
  const article = document.createElement("article");
  article.className = "project-card";
  article.dataset.id = p.id;
  article.style.setProperty("--accent", p.color);

  const pct      = p.completion_pct  ?? 0;
  const wipPct   = p.in_progress_pct ?? 0;
  const done     = p.done_count      ?? 0;
  const wip      = p.in_progress_count ?? 0;
  const total    = p.task_count      ?? 0;

  const metaWip  = wip  ? ` · ${wip} in progress` : "";
  const labelWip = wipPct ? ` · ${wipPct}% in corso` : "";
  const tipText  = `${pct}% done${wipPct ? `, ${wipPct}% in progress` : ""}`;

  article.innerHTML = `
    <div class="project-card__color-bar"></div>
    <div class="project-card__body">
      <h2 class="project-card__name">${escHtml(p.name)}</h2>
      <p class="project-card__meta">${total} task${total !== 1 ? "s" : ""} &middot; ${done} done${metaWip}</p>
      <div class="progress-wrap" title="${tipText}">
        <div class="progress-bar" style="width: ${pct}%"></div>
        <div class="progress-bar progress-bar--wip" style="width: ${wipPct}%; left: ${pct}%"></div>
      </div>
      <p class="progress-label">${pct}% completato${labelWip}</p>
    </div>
    <div class="project-card__footer">
      <a href="/project/${p.id}" class="btn btn--ghost btn--sm">Open board →</a>
      <div class="project-card__actions">
        <button class="icon-btn rename-btn" title="Rename"
          data-id="${p.id}" data-name="${escHtml(p.name)}" data-color="${p.color}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>
        <button class="icon-btn delete-btn" title="Delete"
          data-id="${p.id}" data-name="${escHtml(p.name)}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14H6L5 6"/>
            <path d="M10 11v6M14 11v6"/>
            <path d="M9 6V4h6v2"/>
          </svg>
        </button>
      </div>
    </div>`;

  return article;
}

/** Minimal HTML-escape helper */
function escHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c])
  );
}

function removeEmptyState() {
  const es = document.getElementById("empty-state");
  if (es) es.remove();
}

function maybeShowEmptyState() {
  const cards = grid.querySelectorAll(".project-card");
  if (cards.length === 0 && !document.getElementById("empty-state")) {
    const div = document.createElement("div");
    div.id = "empty-state";
    div.className = "empty-state";
    div.innerHTML = `<div class="empty-state__icon">📋</div><p class="empty-state__text">No projects yet.<br>Create your first board!</p>`;
    grid.appendChild(div);
  }
}

/* ── CRUD operations ─────────────────────────────────────────────────────── */

async function saveProject() {
  const name = pmNameInput.value.trim();
  if (!name) { pmNameInput.focus(); return; }

  pmSaveBtn.disabled = true;
  try {
    if (_editingProjectId) {
      // Rename
      const updated = await api(`/api/projects/${_editingProjectId}`, "PUT", { name, color: _selectedColor });
      const card = grid.querySelector(`[data-id="${_editingProjectId}"]`);
      if (card) {
        card.style.setProperty("--accent", updated.color);
        card.querySelector(".project-card__name").textContent = updated.name;
        card.querySelector(".rename-btn").dataset.name = updated.name;
        card.querySelector(".rename-btn").dataset.color = updated.color;
        card.querySelector(".delete-btn").dataset.name = updated.name;
      }
      showToast("Project renamed ✓");
    } else {
      // Create
      const proj = await api("/api/projects", "POST", { name, color: _selectedColor });
      removeEmptyState();
      const card = buildProjectCard({ ...proj, task_count: 0, done_count: 0, completion_pct: 0 });
      grid.insertBefore(card, grid.firstChild);
      applyProgressState(card);
      showToast("Project created ✓");
    }
    closeProjectModal();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    pmSaveBtn.disabled = false;
  }
}

async function deleteProject(id) {
  try {
    await api(`/api/projects/${id}`, "DELETE");
    const card = grid.querySelector(`[data-id="${id}"]`);
    if (card) {
      card.style.opacity = "0";
      card.style.transform = "scale(.9)";
      card.style.transition = "opacity .2s, transform .2s";
      setTimeout(() => { card.remove(); maybeShowEmptyState(); }, 200);
    }
    showToast("Project deleted");
  } catch (err) {
    showToast(err.message, "error");
  }
}

/* ── Event wiring ────────────────────────────────────────────────────────── */

// New project button
btnNewProject.addEventListener("click", () => openProjectModal());

// Colour swatches
colorSwatches.forEach(swatch => {
  swatch.addEventListener("click", () => {
    colorSwatches.forEach(s => s.classList.remove("active"));
    swatch.classList.add("active");
    _selectedColor = swatch.dataset.color;
  });
});

// Modal save / cancel
pmSaveBtn.addEventListener("click", saveProject);
pmCancelBtn.addEventListener("click", closeProjectModal);
pmCloseBtn.addEventListener("click", closeProjectModal);
pmNameInput.addEventListener("keydown", e => { if (e.key === "Enter") saveProject(); });

// Rename / delete buttons (event delegation on grid)
grid.addEventListener("click", e => {
  const renameBtn = e.target.closest(".rename-btn");
  const deleteBtn = e.target.closest(".delete-btn");

  if (renameBtn) {
    openProjectModal(
      Number(renameBtn.dataset.id),
      renameBtn.dataset.name,
      renameBtn.dataset.color
    );
  }

  if (deleteBtn) {
    _pendingDeleteId = Number(deleteBtn.dataset.id);
    confirmMsg.textContent = `Delete "${deleteBtn.dataset.name}"? All tasks will be permanently removed.`;
    openModal("confirm-modal");
  }
});

// Confirm delete modal
confirmDelete.addEventListener("click", async () => {
  if (!_pendingDeleteId) return;
  closeModal("confirm-modal");
  await deleteProject(_pendingDeleteId);
  _pendingDeleteId = null;
});
confirmCancel.addEventListener("click", () => closeModal("confirm-modal"));
confirmClose.addEventListener("click",  () => closeModal("confirm-modal"));
