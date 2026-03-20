"""
KanFlow – Git & filesystem utilities
Uses only Python built-ins: subprocess, os, pathlib.
No gitpython or other dependencies required.
"""

import os
import subprocess
from pathlib import Path

# Extensions considered "source files" for the tree browser
SOURCE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte",
    ".html", ".css", ".scss", ".sass", ".less",
    ".java", ".kt", ".scala",
    ".c", ".cpp", ".h", ".hpp",
    ".cs", ".vb",
    ".go", ".rs", ".zig",
    ".rb", ".php", ".lua", ".r",
    ".sh", ".bash", ".zsh", ".fish", ".ps1",
    ".sql", ".graphql",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".env", ".cfg", ".conf",
    ".md", ".rst", ".txt",
    ".dockerfile", ".makefile",
}

# Directories always excluded from browsing
EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    "dist", "build", "out", ".next", ".nuxt",
    ".idea", ".vscode", ".vs",
    "coverage", ".nyc_output",
}


# ── Validation ────────────────────────────────────────────────────────────────

def validate_git_repo(path: str) -> dict:
    """
    Check whether `path` is a valid, accessible git repository.

    Returns:
        {"ok": True,  "branch": str, "remote": str | None}
        {"ok": False, "error": str}
    """
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"Percorso non trovato: {path}"}
    if not p.is_dir():
        return {"ok": False, "error": "Il percorso non è una cartella"}
    if not (p / ".git").exists():
        return {"ok": False, "error": "Nessun repository git trovato (manca la cartella .git)"}

    # Read current branch
    branch = _run_git(path, ["rev-parse", "--abbrev-ref", "HEAD"])
    if branch is None:
        return {"ok": False, "error": "Impossibile leggere il branch git corrente"}

    # Read remote origin (optional)
    remote = _run_git(path, ["remote", "get-url", "origin"])

    return {"ok": True, "branch": branch.strip(), "remote": (remote or "").strip() or None}


# ── File tree ─────────────────────────────────────────────────────────────────

def get_file_tree(repo_path: str, subdir: str = "") -> dict:
    """
    Return a directory listing (one level) for the repo.

    Args:
        repo_path: Absolute path to git root.
        subdir:    Relative subpath inside the repo (empty = root).

    Returns:
        {
          "path":    relative path shown in breadcrumb,
          "entries": [{"name": str, "rel_path": str, "type": "dir"|"file",
                       "ext": str, "size": int}, …]
        }
    """
    root   = Path(repo_path).resolve()
    target = (root / subdir).resolve() if subdir else root

    # Security: never escape the repo root
    try:
        target.relative_to(root)
    except ValueError:
        return {"path": "", "entries": []}

    if not target.is_dir():
        return {"path": subdir, "entries": []}

    entries = []
    try:
        items = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return {"path": subdir, "entries": []}

    for item in items:
        if item.name.startswith(".") and item.name != ".env":
            continue
        if item.is_dir() and item.name in EXCLUDED_DIRS:
            continue

        rel = str(item.relative_to(root)).replace("\\", "/")

        if item.is_dir():
            entries.append({"name": item.name, "rel_path": rel, "type": "dir", "ext": "", "size": 0})
        elif item.is_file():
            ext = item.suffix.lower()
            if ext in SOURCE_EXTS or item.suffix == "":
                try:
                    size = item.stat().st_size
                except OSError:
                    size = 0
                entries.append({"name": item.name, "rel_path": rel, "type": "file", "ext": ext, "size": size})

    return {"path": subdir, "entries": entries}


# ── Git status ────────────────────────────────────────────────────────────────

# Map git porcelain XY codes → human label
_GIT_STATUS_MAP = {
    "M": "modified",
    "A": "added",
    "D": "deleted",
    "R": "renamed",
    "C": "copied",
    "U": "conflict",
    "?": "untracked",
    " ": "clean",
}


def get_git_status(repo_path: str, rel_paths: list[str]) -> dict[str, str]:
    """
    Return git status for a list of relative file paths.

    Returns: {rel_path: status_label}
    where status_label ∈ {"clean","modified","added","deleted","renamed","untracked","conflict","unknown"}
    """
    if not rel_paths:
        return {}

    raw = _run_git(repo_path, ["status", "--porcelain", "-u"] + rel_paths)
    if raw is None:
        return {p: "unknown" for p in rel_paths}

    status_map: dict[str, str] = {p: "clean" for p in rel_paths}

    for line in raw.splitlines():
        if len(line) < 4:
            continue
        xy       = line[:2]
        filepath = line[3:].strip().replace("\\", "/")
        # Porcelain: XY where X=index, Y=worktree; '?' = untracked
        code = xy[1] if xy[1] != " " else xy[0]
        label = _GIT_STATUS_MAP.get(code, "unknown")
        # Match against our relative paths (handle renamed "old -> new")
        for p in rel_paths:
            if p in filepath:
                status_map[p] = label

    return status_map


def get_recent_commits(repo_path: str, rel_path: str, n: int = 5) -> list[dict]:
    """
    Return the last `n` commits that touched `rel_path`.

    Each entry: {"hash": str, "date": str, "author": str, "message": str}
    """
    fmt  = "%H|%ad|%an|%s"
    raw  = _run_git(
        repo_path,
        ["log", f"-{n}", f"--format={fmt}", "--date=short", "--", rel_path]
    )
    if not raw:
        return []

    result = []
    for line in raw.strip().splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            result.append({
                "hash":    parts[0][:8],
                "date":    parts[1],
                "author":  parts[2],
                "message": parts[3],
            })
    return result


def get_all_files_in_dir(repo_path: str, rel_dir: str) -> list[str]:
    """
    Recursively collect all source-file relative paths under `rel_dir`.
    Respects EXCLUDED_DIRS and SOURCE_EXTS filters.
    Returns a flat list of rel_paths (forward-slash separated).
    """
    root   = Path(repo_path).resolve()
    target = (root / rel_dir).resolve() if rel_dir else root

    try:
        target.relative_to(root)
    except ValueError:
        return []

    result = []
    _walk_dir(root, target, result)
    return result


def _walk_dir(root: Path, current: Path, result: list):
    try:
        items = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return
    for item in items:
        if item.name.startswith(".") and item.name != ".env":
            continue
        if item.is_dir():
            if item.name in EXCLUDED_DIRS:
                continue
            _walk_dir(root, item, result)
        elif item.is_file():
            if item.suffix.lower() in SOURCE_EXTS or item.suffix == "":
                result.append(str(item.relative_to(root)).replace("\\", "/"))


# ── Internal helpers ──────────────────────────────────────────────────────────

def _run_git(cwd: str, args: list[str]) -> str | None:
    """Run a git command in `cwd`; return stdout or None on error."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
