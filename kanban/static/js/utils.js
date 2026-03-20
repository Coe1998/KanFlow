/**
 * KanFlow – Shared utilities
 * Loaded on every page via base.html
 */

/* ── API helpers ─────────────────────────────────────────────────────────── */

/**
 * Thin wrapper around fetch that always sends/receives JSON.
 * @param {string} url
 * @param {string} method  GET | POST | PUT | DELETE
 * @param {object} [body]  payload (omit for GET/DELETE with no body)
 * @returns {Promise<object>}
 */
async function api(url, method = "GET", body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);

  const res = await fetch(url, opts);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

/* ── Toast notification ──────────────────────────────────────────────────── */

let _toastTimer = null;

/**
 * Show a brief toast message at the bottom-right corner.
 * @param {string} msg
 * @param {"success"|"error"} [type]
 * @param {number} [duration=2800]
 */
function showToast(msg, type = "success", duration = 2800) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast toast--${type} show`;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { el.classList.remove("show"); }, duration);
}

/* ── Modal helpers ───────────────────────────────────────────────────────── */

/**
 * Open a modal and show the backdrop.
 * @param {string} modalId  – id of the .modal element
 */
function openModal(modalId) {
  const modal    = document.getElementById(modalId);
  const backdrop = document.getElementById("modal-backdrop");
  if (!modal) return;
  modal.classList.remove("hidden");
  backdrop.classList.remove("hidden");
  // focus first input for accessibility
  const first = modal.querySelector("input, textarea, button");
  if (first) setTimeout(() => first.focus(), 50);
}

/**
 * Close a modal and hide the backdrop (unless another modal is still open).
 * @param {string} modalId
 */
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add("hidden");

  // only hide backdrop when no other modal is visible
  const anyOpen = [...document.querySelectorAll(".modal")].some(
    m => !m.classList.contains("hidden")
  );
  if (!anyOpen) {
    document.getElementById("modal-backdrop").classList.add("hidden");
  }
}

/** Close all modals. */
function closeAllModals() {
  document.querySelectorAll(".modal").forEach(m => m.classList.add("hidden"));
  document.getElementById("modal-backdrop").classList.add("hidden");
}

/* Close on backdrop click */
document.getElementById("modal-backdrop").addEventListener("click", closeAllModals);

/* Close on Escape */
document.addEventListener("keydown", e => {
  if (e.key === "Escape") closeAllModals();
});
