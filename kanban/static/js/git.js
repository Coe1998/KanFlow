/**
 * KanFlow – Git & File Drawer (board page)
 */

"use strict";

/* ── DOM refs ────────────────────────────────────────────────────────────── */

const gitBtn          = document.getElementById("btn-git");
const gitDotEl        = document.getElementById("git-dot");
const gitBackdropEl   = document.getElementById("git-backdrop");
const gitDrawerEl     = document.getElementById("git-drawer");
const gitDrawerCloseEl= document.getElementById("git-drawer-close");

const gitPathInputEl  = document.getElementById("git-path-input");
const gitPathSaveEl   = document.getElementById("git-path-save");
const gitStatusBadgeEl= document.getElementById("git-status-badge");

const gitPinnedListEl = document.getElementById("git-pinned-list");
const gitPinnedEmptyEl= document.getElementById("git-pinned-empty");
const gitRefreshBtnEl = document.getElementById("git-refresh-btn");

const gitBrowserEl    = document.getElementById("git-browser");
const gitBreadcrumbEl = document.getElementById("git-breadcrumb");

/* ── State ───────────────────────────────────────────────────────────────── */

let _gitRepoPath  = "";
let _gitCurrentDir= "";
let _gitPinned    = [];
let _gitStatus    = {};
let _gitOpen      = false;

/* ── Status styles ───────────────────────────────────────────────────────── */

const GIT_STATUS_META = {
  clean:     { cls: "status-clean",     icon: "✓", label: "clean"     },
  modified:  { cls: "status-modified",  icon: "M", label: "modified"  },
  added:     { cls: "status-added",     icon: "A", label: "added"     },
  deleted:   { cls: "status-deleted",   icon: "D", label: "deleted"   },
  renamed:   { cls: "status-renamed",   icon: "R", label: "renamed"   },
  untracked: { cls: "status-untracked", icon: "?", label: "untracked" },
  conflict:  { cls: "status-conflict",  icon: "!", label: "conflict"  },
  unknown:   { cls: "status-unknown",   icon: "·", label: "—"         },
};
function _gitStatusMeta(s) { return GIT_STATUS_META[s] ?? GIT_STATUS_META.unknown; }

const GIT_FILE_ICONS = {
  ".py":"🐍",".js":"🟨",".ts":"🔷",".jsx":"⚛️",".tsx":"⚛️",
  ".html":"🌐",".css":"🎨",".scss":"🎨",".json":"📋",
  ".md":"📝",".txt":"📄",".sh":"⚙️",".sql":"🗄️",
  ".yaml":"📋",".yml":"📋",".toml":"📋",".env":"🔑",
  ".cs":"💠",".java":"☕",".go":"🐹",".rs":"🦀",
  ".cpp":"⚙️",".c":"⚙️",".rb":"💎",".php":"🐘",
};
function _gitFileIcon(ext) { return GIT_FILE_ICONS[ext] || "📄"; }

/* ── Helpers ─────────────────────────────────────────────────────────────── */

function _gitEsc(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c])
  );
}

function _gitUpdateDot(hasRepo) {
  gitDotEl.classList.toggle("hidden", !hasRepo);
  gitBtn.classList.toggle("has-git", hasRepo);
}

/* ── Open / close ────────────────────────────────────────────────────────── */

function openGitDrawer() {
  _gitOpen = true;
  // Use rAF so both backdrop and drawer animate together, avoiding
  // the backdrop intercepting the originating click event.
  requestAnimationFrame(() => {
    gitBackdropEl.classList.remove("hidden");
    gitDrawerEl.classList.add("open");
  });
  loadGitInfo();
}

function closeGitDrawer() {
  _gitOpen = false;
  gitDrawerEl.classList.remove("open");
  gitBackdropEl.classList.add("hidden");
}

/* ── Load from API ───────────────────────────────────────────────────────── */

async function loadGitInfo() {
  try {
    const info = await api(`/api/projects/${PROJECT_ID}/git`);
    _gitRepoPath = info.git_path || "";
    gitPathInputEl.value = _gitRepoPath;
    renderGitStatusBadge(info);
    _gitUpdateDot(!!_gitRepoPath);
  } catch (_) {}
  await loadGitPinnedFiles();
  if (_gitRepoPath) await gitBrowseDir("");
}

async function loadGitPinnedFiles() {
  try {
    _gitPinned = await api(`/api/projects/${PROJECT_ID}/files`);
    await refreshAllGitStatus();
  } catch (_) { _gitPinned = []; }
  renderGitPinnedFiles();
}

async function refreshAllGitStatus() {
  if (!_gitRepoPath || !_gitPinned.length) { _gitStatus = {}; return; }
  try {
    _gitStatus = await api(`/api/projects/${PROJECT_ID}/git/status`);
  } catch (_) { _gitStatus = {}; }
}

/* ── Repo path ───────────────────────────────────────────────────────────── */

async function saveGitPath() {
  const path = gitPathInputEl.value.trim();
  gitPathSaveEl.disabled = true;
  try {
    const info = await api(`/api/projects/${PROJECT_ID}/git`, "PATCH", { git_path: path });
    _gitRepoPath = path;
    renderGitStatusBadge(info);
    _gitUpdateDot(!!path);
    showToast(path ? "Repository collegato ✓" : "Repository rimosso");
    _gitCurrentDir = "";
    if (path) await gitBrowseDir("");
    else gitBrowserEl.innerHTML = `<p class="git-empty-msg">Collega un repository per sfogliarne i file.</p>`;
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    gitPathSaveEl.disabled = false;
  }
}

function renderGitStatusBadge(info) {
  gitStatusBadgeEl.classList.remove("hidden");
  if (info.ok) {
    gitStatusBadgeEl.className = "git-status-badge git-status-badge--ok";
    gitStatusBadgeEl.innerHTML =
      `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
       Branch: <strong>${_gitEsc(info.branch)}</strong>
       ${info.remote ? `<span class="git-remote">${_gitEsc(info.remote)}</span>` : ""}`;
  } else if (info.error) {
    gitStatusBadgeEl.className = "git-status-badge git-status-badge--err";
    gitStatusBadgeEl.innerHTML =
      `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
       ${_gitEsc(info.error)}`;
  } else {
    gitStatusBadgeEl.classList.add("hidden");
  }
}

/* ── File browser ────────────────────────────────────────────────────────── */

async function gitBrowseDir(subdir) {
  if (!_gitRepoPath) return;
  _gitCurrentDir = subdir;
  gitBreadcrumbEl.textContent = "/" + subdir;
  gitBrowserEl.innerHTML = `<p class="git-empty-msg git-loading">Caricamento…</p>`;
  try {
    const tree = await api(`/api/projects/${PROJECT_ID}/git/browse?path=${encodeURIComponent(subdir)}`);
    renderGitBrowser(tree);
  } catch (err) {
    gitBrowserEl.innerHTML = `<p class="git-empty-msg">Errore: ${_gitEsc(err.message)}</p>`;
  }
}

function renderGitBrowser(tree) {
  gitBrowserEl.innerHTML = "";
  const pinnedSet = new Set(_gitPinned.map(f => f.rel_path));

  if (_gitCurrentDir) {
    const parent = _gitCurrentDir.split("/").filter(Boolean).slice(0, -1).join("/");
    const back = document.createElement("div");
    back.className = "git-entry git-entry--back";
    back.innerHTML = `<span class="git-entry__icon">←</span><span class="git-entry__name">..</span>`;
    back.addEventListener("click", () => gitBrowseDir(parent));
    gitBrowserEl.appendChild(back);
  }

  if (!tree.entries || !tree.entries.length) {
    gitBrowserEl.innerHTML += `<p class="git-empty-msg">Cartella vuota.</p>`;
    return;
  }

  tree.entries.forEach(entry => {
    const el = document.createElement("div");
    el.className = `git-entry git-entry--${entry.type}`;

    if (entry.type === "dir") {
      const isPinned = pinnedSet.has(entry.rel_path);
      el.innerHTML = `
        <span class="git-entry__icon">📁</span>
        <span class="git-entry__name">${_gitEsc(entry.name)}</span>
        <button class="git-pin-btn ${isPinned ? "pinned" : ""}"
                title="${isPinned ? "Rimuovi pin cartella" : "Pinna intera cartella"}">
          ${isPinned ? "📌" : "📍"}
        </button>
        <span class="git-entry__arrow">›</span>`;

      // Pin button — stop propagation so folder doesn't navigate
      el.querySelector(".git-pin-btn").addEventListener("click", async e => {
        e.stopPropagation();
        if (pinnedSet.has(entry.rel_path)) await gitUnpinFile(entry.rel_path);
        else await gitPinFile(entry.rel_path, true);   // is_dir = true
        await gitBrowseDir(_gitCurrentDir);
      });

      // Navigate into folder on row click (but not on pin button)
      el.addEventListener("click", e => {
        if (e.target.closest(".git-pin-btn")) return;
        gitBrowseDir(entry.rel_path);
      });

    } else {
      const isPinned = pinnedSet.has(entry.rel_path);
      const size = entry.size > 1024 ? (entry.size/1024).toFixed(1)+" KB" : entry.size+" B";
      el.innerHTML = `
        <span class="git-entry__icon">${_gitFileIcon(entry.ext)}</span>
        <span class="git-entry__name">${_gitEsc(entry.name)}</span>
        <span class="git-entry__size">${size}</span>
        <button class="git-pin-btn ${isPinned ? "pinned" : ""}"
                title="${isPinned ? "Rimuovi pin" : "Aggiungi pin"}">
          ${isPinned ? "📌" : "📍"}
        </button>`;
      el.querySelector(".git-pin-btn").addEventListener("click", async e => {
        e.stopPropagation();
        if (pinnedSet.has(entry.rel_path)) await gitUnpinFile(entry.rel_path);
        else await gitPinFile(entry.rel_path, false);  // is_dir = false
        await gitBrowseDir(_gitCurrentDir);
      });
    }
    gitBrowserEl.appendChild(el);
  });
}

/* ── Pinned files ────────────────────────────────────────────────────────── */

async function gitPinFile(relPath, isDir = false) {
  try {
    const f = await api(`/api/projects/${PROJECT_ID}/files`, "POST",
                        { rel_path: relPath, is_dir: isDir });
    _gitPinned.push(f);
    await refreshAllGitStatus();
    renderGitPinnedFiles();
    _gitUpdateDot(true);
    const label = isDir ? `📁 ${relPath.split("/").pop()}/` : relPath.split("/").pop();
    showToast(`📌 ${label} aggiunto`);
  } catch (err) { showToast(err.message, "error"); }
}

async function gitUnpinFile(relPath) {
  try {
    await api(`/api/projects/${PROJECT_ID}/files/${encodeURIComponent(relPath)}`, "DELETE");
    _gitPinned = _gitPinned.filter(f => f.rel_path !== relPath);
    delete _gitStatus[relPath];
    renderGitPinnedFiles();
    showToast("Pin rimosso");
  } catch (err) { showToast(err.message, "error"); }
}

function renderGitPinnedFiles() {
  gitPinnedListEl.querySelectorAll(".git-pinned-item").forEach(el => el.remove());
  gitPinnedEmptyEl.classList.toggle("hidden", _gitPinned.length > 0);

  _gitPinned.forEach(file => {
    const status   = _gitStatus[file.rel_path] || (file.is_dir ? "unknown" : "unknown");
    const meta     = _gitStatusMeta(status);
    const isDir    = !!file.is_dir;
    const basename = file.rel_path.split("/").pop();
    const dirPart  = file.rel_path.includes("/")
      ? file.rel_path.substring(0, file.rel_path.lastIndexOf("/")) : "";

    const item = document.createElement("div");
    item.className = "git-pinned-item";

    item.innerHTML = `
      <div class="git-pinned-item__row">
        <span class="git-pinned-item__type-icon">${isDir ? "📁" : "📄"}</span>
        ${isDir ? "" : `<span class="git-status-dot ${meta.cls}" title="${meta.label}">${meta.icon}</span>`}
        <div class="git-pinned-item__info">
          <span class="git-pinned-item__name">${_gitEsc(basename)}${isDir ? "/" : ""}</span>
          ${isDir
            ? `<span class="git-pinned-item__dir git-pinned-item__dir--folder">cartella intera</span>`
            : dirPart ? `<span class="git-pinned-item__dir">${_gitEsc(dirPart)}</span>` : ""}
        </div>
        <div class="git-pinned-item__actions">
          ${!isDir ? `<button class="git-commits-btn" title="Ultimi commit">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><line x1="1.05" y1="12" x2="7" y2="12"/><line x1="17.01" y1="12" x2="22.96" y2="12"/></svg>
          </button>` : ""}
          <button class="git-unpin-btn" title="Rimuovi pin">✕</button>
        </div>
      </div>
      <div class="git-commits-panel hidden"></div>`;

    item.querySelector(".git-unpin-btn").addEventListener("click", async () => {
      await gitUnpinFile(file.rel_path);
      if (_gitRepoPath) await gitBrowseDir(_gitCurrentDir);
    });

    item.querySelector(".git-commits-btn").addEventListener("click", async () => {
      const panel = item.querySelector(".git-commits-panel");
      if (!panel.classList.contains("hidden")) { panel.classList.add("hidden"); return; }
      panel.classList.remove("hidden");
      panel.innerHTML = `<p class="git-empty-msg git-loading">Caricamento commit…</p>`;
      try {
        const commits = await api(`/api/projects/${PROJECT_ID}/git/commits?path=${encodeURIComponent(file.rel_path)}`);
        renderGitCommits(panel, commits);
      } catch (err) {
        panel.innerHTML = `<p class="git-empty-msg">Errore: ${_gitEsc(err.message)}</p>`;
      }
    });

    gitPinnedListEl.insertBefore(item, gitPinnedEmptyEl);
  });
}

function renderGitCommits(container, commits) {
  if (!commits.length) {
    container.innerHTML = `<p class="git-empty-msg">Nessun commit trovato per questo file.</p>`;
    return;
  }
  container.innerHTML = commits.map(c => `
    <div class="git-commit">
      <span class="git-commit__hash">${_gitEsc(c.hash)}</span>
      <span class="git-commit__date">${_gitEsc(c.date)}</span>
      <span class="git-commit__msg">${_gitEsc(c.message)}</span>
    </div>`).join("");
}

/* ── Event wiring ────────────────────────────────────────────────────────── */

gitBtn.addEventListener("click", openGitDrawer);
gitDrawerCloseEl.addEventListener("click", closeGitDrawer);
gitBackdropEl.addEventListener("click", closeGitDrawer);
gitPathSaveEl.addEventListener("click", saveGitPath);
gitPathInputEl.addEventListener("keydown", e => { if (e.key === "Enter") saveGitPath(); });
gitRefreshBtnEl.addEventListener("click", async () => {
  await refreshAllGitStatus();
  renderGitPinnedFiles();
  showToast("Status aggiornato");
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && _gitOpen) closeGitDrawer();
});

/* ── Init: show dot if repo already linked ───────────────────────────────── */
(async () => {
  try {
    const info = await api(`/api/projects/${PROJECT_ID}/git`);
    if (info.git_path) _gitUpdateDot(true);
  } catch (_) {}
})();
