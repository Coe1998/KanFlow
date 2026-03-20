/**
 * KanFlow – Project Notes Drawer
 *
 * Features:
 *  - Slide-in drawer from the right
 *  - Markdown-lite renderer (headings, bold, italic, inline code,
 *    fenced code blocks with language label + copy button, lists,
 *    blockquotes, horizontal rules)
 *  - Toolbar shortcuts for common formatting
 *  - Keyboard shortcuts: Ctrl+B, Ctrl+I, Ctrl+S, Ctrl+`
 *  - Auto-save via debounced PATCH call (3 s after last keystroke)
 *  - Unsaved indicator in header
 */

"use strict";

/* ── DOM refs ────────────────────────────────────────────────────────────── */

const btnNotes       = document.getElementById("btn-notes");
const notesDot       = document.getElementById("notes-dot");
const notesBackdrop  = document.getElementById("notes-backdrop");
const notesDrawer    = document.getElementById("notes-drawer");
const notesClose     = document.getElementById("notes-drawer-close");
const notesTextarea  = document.getElementById("notes-textarea");
const notesRendered  = document.getElementById("notes-rendered");
const notesSaveBtn   = document.getElementById("notes-save-btn");
const notesSaveStatus= document.getElementById("notes-save-status");
const notesCharCount = document.getElementById("notes-char-count");

const bodyEdit       = document.getElementById("notes-body-edit");
const bodyPreview    = document.getElementById("notes-body-preview");
const btnModeEdit    = document.getElementById("btn-mode-edit");
const btnModePreview = document.getElementById("btn-mode-preview");
const notesToolbar   = document.getElementById("notes-toolbar");

/* ── State ───────────────────────────────────────────────────────────────── */

let _savedContent  = "";   // last successfully saved value
let _autoSaveTimer = null;
let _isSaving      = false;
let _drawerOpen    = false;

/* ── Open / close drawer ─────────────────────────────────────────────────── */

async function openNotesDrawer() {
  _drawerOpen = true;
  requestAnimationFrame(() => {
    notesBackdrop.classList.remove("hidden");
    notesDrawer.classList.add("open");
  });
  await loadNotes();
  notesTextarea.focus();
}

function closeNotesDrawer() {
  _drawerOpen = false;
  notesDrawer.classList.remove("open");
  notesBackdrop.classList.add("hidden");
  // Flush any pending auto-save immediately
  if (_autoSaveTimer) {
    clearTimeout(_autoSaveTimer);
    _autoSaveTimer = null;
    if (notesTextarea.value !== _savedContent) saveNotes();
  }
}

/* ── Load notes from API ─────────────────────────────────────────────────── */

async function loadNotes() {
  try {
    const data = await api(`/api/projects/${PROJECT_ID}/notes`);
    _savedContent = data.notes || "";
    notesTextarea.value = _savedContent;
    updateCharCount();
    setSaveStatus("saved");
    updateHeaderDot(_savedContent);
  } catch (err) {
    showToast("Impossibile caricare le note: " + err.message, "error");
  }
}

/* ── Save notes to API ───────────────────────────────────────────────────── */

async function saveNotes() {
  if (_isSaving) return;
  const content = notesTextarea.value;
  if (content === _savedContent) { setSaveStatus("saved"); return; }

  _isSaving = true;
  setSaveStatus("saving");
  notesSaveBtn.disabled = true;

  try {
    await api(`/api/projects/${PROJECT_ID}/notes`, "PATCH", { notes: content });
    _savedContent = content;
    setSaveStatus("saved");
    updateHeaderDot(content);
    showToast("Note salvate ✓");
  } catch (err) {
    setSaveStatus("unsaved");
    showToast("Errore salvataggio: " + err.message, "error");
  } finally {
    _isSaving = false;
    notesSaveBtn.disabled = false;
  }
}

function scheduleAutoSave() {
  setSaveStatus("unsaved");
  clearTimeout(_autoSaveTimer);
  _autoSaveTimer = setTimeout(saveNotes, 3000);
}

/* ── Status helpers ──────────────────────────────────────────────────────── */

function setSaveStatus(state) {
  // state: "saved" | "unsaved" | "saving"
  const labels = { saved: "salvato", unsaved: "non salvato", saving: "salvataggio…" };
  notesSaveStatus.textContent = labels[state] ?? "";
  notesSaveStatus.className   = `notes-save-status ${state}`;
}

function updateCharCount() {
  const n = notesTextarea.value.length;
  notesCharCount.textContent = `${n.toLocaleString("it")} caratteri`;
}

/** Show/hide the amber dot on the board header "Note" button. */
function updateHeaderDot(content) {
  const hasContent = content.trim().length > 0;
  notesDot.classList.toggle("hidden", !hasContent);
  btnNotes.classList.toggle("has-notes", hasContent);
}

/* ── Markdown-lite renderer ──────────────────────────────────────────────── */

/**
 * Converts a small subset of Markdown to safe HTML.
 * Supported: headings (#/##/###), **bold**, *italic*, `inline code`,
 * fenced code blocks (```lang ... ```), - / * bullet lists, ordered lists,
 * > blockquotes, --- horizontal rules.
 */
function renderMarkdown(text) {
  // Escape HTML first to prevent XSS
  function esc(s) {
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  const lines    = text.split("\n");
  const html     = [];
  let inCode     = false;
  let codeLang   = "";
  let codeLines  = [];
  let inList     = null;   // "ul" | "ol" | null
  let listHtml   = [];

  function flushList() {
    if (!inList) return;
    html.push(`<${inList}>${listHtml.join("")}</${inList}>`);
    inList   = null;
    listHtml = [];
  }

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];

    // ── Fenced code block ─────────────────────────────────────────────────
    if (!inCode && /^```/.test(raw)) {
      flushList();
      inCode   = true;
      codeLang = raw.slice(3).trim();
      codeLines = [];
      continue;
    }
    if (inCode) {
      if (/^```/.test(raw)) {
        // close block
        const langLabel = codeLang
          ? `<span class="notes-codeblock__lang">${esc(codeLang)}</span>`
          : "";
        const codeContent = esc(codeLines.join("\n"));
        html.push(`
          <div class="notes-codeblock">
            ${langLabel}
            <button class="notes-codeblock__copy" onclick="copyCode(this)">copia</button>
            <pre><code>${codeContent}</code></pre>
          </div>`);
        inCode = false; codeLang = ""; codeLines = [];
      } else {
        codeLines.push(raw);
      }
      continue;
    }

    // ── List items ────────────────────────────────────────────────────────
    const ulMatch = raw.match(/^(\s*)[-*+]\s+(.+)/);
    const olMatch = raw.match(/^(\s*)\d+\.\s+(.+)/);

    if (ulMatch) {
      if (inList !== "ul") { flushList(); inList = "ul"; }
      listHtml.push(`<li>${inlineRender(esc(ulMatch[2]))}</li>`);
      continue;
    }
    if (olMatch) {
      if (inList !== "ol") { flushList(); inList = "ol"; }
      listHtml.push(`<li>${inlineRender(esc(olMatch[2]))}</li>`);
      continue;
    }
    flushList();

    // ── Headings ──────────────────────────────────────────────────────────
    const h3 = raw.match(/^###\s+(.*)/);
    const h2 = raw.match(/^##\s+(.*)/);
    const h1 = raw.match(/^#\s+(.*)/);
    if (h3) { html.push(`<h3>${inlineRender(esc(h3[1]))}</h3>`); continue; }
    if (h2) { html.push(`<h2>${inlineRender(esc(h2[1]))}</h2>`); continue; }
    if (h1) { html.push(`<h1>${inlineRender(esc(h1[1]))}</h1>`); continue; }

    // ── Blockquote ────────────────────────────────────────────────────────
    const bq = raw.match(/^>\s*(.*)/);
    if (bq) { html.push(`<blockquote>${inlineRender(esc(bq[1]))}</blockquote>`); continue; }

    // ── Horizontal rule ───────────────────────────────────────────────────
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(raw.trim())) {
      html.push("<hr>"); continue;
    }

    // ── Blank line ────────────────────────────────────────────────────────
    if (raw.trim() === "") { html.push("<p></p>"); continue; }

    // ── Paragraph ─────────────────────────────────────────────────────────
    html.push(`<p>${inlineRender(esc(raw))}</p>`);
  }

  flushList();
  return html.join("\n");
}

/** Apply inline formatting: bold, italic, inline code, links. */
function inlineRender(s) {
  return s
    .replace(/`([^`]+)`/g,    "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>")
    .replace(/__(.+?)__/g,    "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g,    "<em>$1</em>")
    .replace(/_([^_]+)_/g,    "<em>$1</em>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

/** Copy code block content to clipboard. */
window.copyCode = function(btn) {
  const code = btn.closest(".notes-codeblock").querySelector("code").textContent;
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = "copiato ✓";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "copìa"; btn.classList.remove("copied"); }, 2000);
  });
};

/* ── View mode toggle ────────────────────────────────────────────────────── */

function setMode(mode) {
  const isEdit = mode === "edit";
  bodyEdit.classList.toggle("hidden",    !isEdit);
  bodyPreview.classList.toggle("hidden",  isEdit);
  notesToolbar.classList.toggle("hidden", !isEdit);
  btnModeEdit.classList.toggle("active",    isEdit);
  btnModePreview.classList.toggle("active", !isEdit);

  if (!isEdit) {
    notesRendered.innerHTML = renderMarkdown(notesTextarea.value);
  } else {
    notesTextarea.focus();
  }
}

/* ── Toolbar insert helpers ──────────────────────────────────────────────── */

/**
 * Wrap the current selection (or insert at cursor) with prefix/suffix.
 */
function wrapSelection(prefix, suffix = prefix, defaultText = "") {
  const el    = notesTextarea;
  const start = el.selectionStart;
  const end   = el.selectionEnd;
  const sel   = el.value.slice(start, end) || defaultText;
  const replacement = `${prefix}${sel}${suffix}`;

  el.setRangeText(replacement, start, end, "select");
  // Adjust selection to just the inner text
  el.selectionStart = start + prefix.length;
  el.selectionEnd   = start + prefix.length + sel.length;
  el.focus();
  scheduleAutoSave();
}

function insertAtLineStart(prefix) {
  const el    = notesTextarea;
  const start = el.selectionStart;
  const lineStart = el.value.lastIndexOf("\n", start - 1) + 1;
  el.setRangeText(prefix, lineStart, lineStart, "end");
  el.focus();
  scheduleAutoSave();
}

const TOOLBAR_ACTIONS = {
  "bold":        () => wrapSelection("**", "**", "testo in grassetto"),
  "italic":      () => wrapSelection("*", "*", "testo in corsivo"),
  "code-inline": () => wrapSelection("`", "`", "codice"),
  "code-block":  () => wrapSelection("```\n", "\n```", "incolla il codice qui"),
  "h2":          () => insertAtLineStart("## "),
  "bullet":      () => insertAtLineStart("- "),
  "clear": () => {
    if (!notesTextarea.value.trim()) return;
    if (!confirm("Cancellare tutto il testo delle note?")) return;
    notesTextarea.value = "";
    updateCharCount();
    scheduleAutoSave();
  },
};

/* ── Event wiring ────────────────────────────────────────────────────────── */

btnNotes.addEventListener("click",  openNotesDrawer);
notesClose.addEventListener("click", closeNotesDrawer);
notesBackdrop.addEventListener("click", closeNotesDrawer);

btnModeEdit.addEventListener("click",    () => setMode("edit"));
btnModePreview.addEventListener("click", () => setMode("preview"));

notesSaveBtn.addEventListener("click", () => {
  clearTimeout(_autoSaveTimer);
  saveNotes();
});

// Toolbar buttons
notesToolbar.addEventListener("click", e => {
  const btn = e.target.closest("[data-action]");
  if (btn) TOOLBAR_ACTIONS[btn.dataset.action]?.();
});

// Textarea events
notesTextarea.addEventListener("input", () => {
  updateCharCount();
  scheduleAutoSave();
});

// Keyboard shortcuts inside textarea
notesTextarea.addEventListener("keydown", e => {
  const mod = e.ctrlKey || e.metaKey;
  if (!mod) return;

  switch (e.key) {
    case "s":
      e.preventDefault();
      clearTimeout(_autoSaveTimer);
      saveNotes();
      break;
    case "b":
      e.preventDefault();
      wrapSelection("**", "**", "testo");
      break;
    case "i":
      e.preventDefault();
      wrapSelection("*", "*", "testo");
      break;
    case "`":
      e.preventDefault();
      wrapSelection("`", "`", "codice");
      break;
  }
});

// Tab key → insert 2 spaces (useful for code blocks)
notesTextarea.addEventListener("keydown", e => {
  if (e.key !== "Tab") return;
  e.preventDefault();
  const s = notesTextarea.selectionStart;
  notesTextarea.setRangeText("  ", s, s, "end");
});

// Close on Escape
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && _drawerOpen) closeNotesDrawer();
});

/* ── Init: show dot if project already has notes ─────────────────────────── */
(async () => {
  try {
    const data = await api(`/api/projects/${PROJECT_ID}/notes`);
    updateHeaderDot(data.notes || "");
  } catch (_) { /* silent — drawer will fetch again when opened */ }
})();
