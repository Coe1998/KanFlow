"""
KanFlow – Documentation Generator
Gathers all project context (tasks, notes, labels, pinned files with content,
git info) and calls Gemini to produce structured Markdown documentation.
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path

import database as db
import git_utils as git

# ── Gemini config (reuses the same model as ai extraction) ────────────────────

GEMINI_MODEL   = "gemini-2.5-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# Max characters to read from each source file (avoid huge context)
MAX_FILE_CHARS = 8_000
# Max total chars of all file contents combined
MAX_TOTAL_FILE_CHARS = 60_000


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
Sei un esperto di documentazione tecnica. Il tuo compito è generare documentazione
professionale e completa per un progetto software sulla base delle informazioni fornite.

REGOLE:
1. Scrivi ESCLUSIVAMENTE in Markdown valido, ben strutturato.
2. Usa heading ##/### (non #, riservato al titolo principale che aggiungiamo noi).
3. Includi TUTTE le sezioni pertinenti tra quelle elencate, ometti solo quelle
   per cui non hai dati sufficienti.
4. Per blocchi di codice usa i fence ``` con il linguaggio specificato.
5. Sii preciso, tecnico e conciso. Niente frasi generiche di riempimento.
6. Se trovi variabili d'ambiente nel codice (os.getenv, process.env, .env) 
   elencale nella sezione dedicata con descrizione e valore di esempio.
7. Per i comandi di installazione/avvio usa blocchi di codice bash.
8. Non inventare funzionalità non presenti nel codice o nei task.

SEZIONI DA INCLUDERE (nell'ordine):
## Descrizione del progetto
## Tecnologie e dipendenze
## Installazione
## Configurazione (variabili d'ambiente)
## Avvio e utilizzo
## Architettura e struttura file
## Funzionalità implementate
## Task in corso / roadmap
## Note tecniche aggiuntive
"""


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_project_docs(project_id: int) -> str:
    """
    Build the full documentation Markdown for a project.

    Returns:
        Markdown string ready to be rendered/converted to PDF.

    Raises:
        RuntimeError: if GOOGLE_API_KEY is missing or Gemini call fails.
    """
    project  = db.get_project(project_id)
    if not project:
        raise RuntimeError(f"Progetto {project_id} non trovato")

    context = _build_context(project)
    prompt  = _build_prompt(project, context)
    markdown = _call_gemini(prompt)

    # Prepend the project title as H1
    title = f"# {project['name']}\n\n"
    return title + markdown


# ── Context builder ───────────────────────────────────────────────────────────

def _build_context(project: dict) -> dict:
    """Collect all relevant data for the prompt."""
    pid = project["id"]

    # Tasks grouped by status
    all_tasks = db.get_tasks(pid)
    tasks_by_status = {
        "done":        [t for t in all_tasks if t["status"] == "done"],
        "in_progress": [t for t in all_tasks if t["status"] == "in_progress"],
        "todo":        [t for t in all_tasks if t["status"] == "todo"],
    }

    # Labels
    labels = db.get_project_labels(pid)

    # Notes
    notes = db.get_project_notes(pid)

    # Git info + pinned files with content
    git_info     = None
    file_contents = {}
    git_path     = (project.get("git_path") or "").strip()

    if git_path:
        validation = git.validate_git_repo(git_path)
        if validation["ok"]:
            git_info = validation
            pinned   = db.get_pinned_files(pid)
            total_chars = 0

            for pf in pinned:
                if total_chars >= MAX_TOTAL_FILE_CHARS:
                    break

                if pf.get("is_dir"):
                    # Expand directory → read every source file inside it
                    file_list = git.get_all_files_in_dir(git_path, pf["rel_path"])
                    for rel in file_list:
                        if total_chars >= MAX_TOTAL_FILE_CHARS:
                            break
                        abs_path = Path(git_path) / rel
                        try:
                            text = abs_path.read_text(encoding="utf-8", errors="replace")
                            if len(text) > MAX_FILE_CHARS:
                                text = text[:MAX_FILE_CHARS] + f"\n... [troncato a {MAX_FILE_CHARS} caratteri]"
                            file_contents[rel] = text
                            total_chars += len(text)
                        except (OSError, IOError):
                            file_contents[rel] = "[impossibile leggere il file]"
                else:
                    # Single file
                    abs_path = Path(git_path) / pf["rel_path"]
                    try:
                        text = abs_path.read_text(encoding="utf-8", errors="replace")
                        if len(text) > MAX_FILE_CHARS:
                            text = text[:MAX_FILE_CHARS] + f"\n... [troncato a {MAX_FILE_CHARS} caratteri]"
                        file_contents[pf["rel_path"]] = text
                        total_chars += len(text)
                    except (OSError, IOError):
                        file_contents[pf["rel_path"]] = "[impossibile leggere il file]"

    return {
        "tasks_by_status": tasks_by_status,
        "labels":          labels,
        "notes":           notes,
        "git_info":        git_info,
        "git_path":        git_path,
        "file_contents":   file_contents,
    }


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(project: dict, ctx: dict) -> str:
    parts = [f"## PROGETTO: {project['name']}\n"]

    # ── Git info ──────────────────────────────────────────────────────────────
    if ctx["git_info"]:
        gi = ctx["git_info"]
        parts.append(f"**Repository git locale:** `{ctx['git_path']}`")
        parts.append(f"**Branch corrente:** `{gi.get('branch','')}`")
        if gi.get("remote"):
            parts.append(f"**Remote origin:** {gi['remote']}")
        parts.append("")

    # ── Labels ────────────────────────────────────────────────────────────────
    if ctx["labels"]:
        label_names = ", ".join(f"`{l['name']}`" for l in ctx["labels"])
        parts.append(f"**Etichette progetto:** {label_names}\n")

    # ── Tasks ─────────────────────────────────────────────────────────────────
    parts.append("### Task completati (DONE)")
    done = ctx["tasks_by_status"]["done"]
    if done:
        for t in done:
            label_str = ""
            if t.get("labels"):
                label_str = " [" + ", ".join(l["name"] for l in t["labels"]) + "]"
            desc = f"\n   {t['description']}" if t.get("description") else ""
            parts.append(f"- {t['title']}{label_str}{desc}")
    else:
        parts.append("*(nessuno)*")
    parts.append("")

    parts.append("### Task in corso (IN PROGRESS)")
    wip = ctx["tasks_by_status"]["in_progress"]
    if wip:
        for t in wip:
            desc = f"\n   {t['description']}" if t.get("description") else ""
            parts.append(f"- {t['title']}{desc}")
    else:
        parts.append("*(nessuno)*")
    parts.append("")

    parts.append("### Task pianificate (TODO)")
    todo = ctx["tasks_by_status"]["todo"]
    if todo:
        for t in todo:
            desc = f"\n   {t['description']}" if t.get("description") else ""
            parts.append(f"- {t['title']}{desc}")
    else:
        parts.append("*(nessuno)*")
    parts.append("")

    # ── Notes ─────────────────────────────────────────────────────────────────
    if ctx["notes"] and ctx["notes"].strip():
        parts.append("### Note del progetto")
        parts.append(ctx["notes"])
        parts.append("")

    # ── File contents ─────────────────────────────────────────────────────────
    if ctx["file_contents"]:
        parts.append("### Contenuto dei file sorgente\n")
        for rel_path, content in ctx["file_contents"].items():
            ext = Path(rel_path).suffix.lstrip(".")
            parts.append(f"**File:** `{rel_path}`")
            parts.append(f"```{ext}")
            parts.append(content)
            parts.append("```")
            parts.append("")

    parts.append(
        "\n---\n"
        "Sulla base di TUTTE le informazioni sopra, genera la documentazione tecnica "
        "completa seguendo le istruzioni di sistema. "
        "Includi una sezione 'Variabili d'ambiente' se trovi chiamate a os.getenv(), "
        "process.env, o file .env nel codice. "
        "Elenca i comandi esatti di installazione e avvio."
    )

    return "\n".join(parts)


# ── Gemini call ───────────────────────────────────────────────────────────────

def _call_gemini(user_prompt: str) -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY non trovata. "
            "Impostala come variabile d'ambiente prima di avviare l'app."
        )

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature":     0.3,
            "maxOutputTokens": 8192,
        },
    }

    url  = f"{GEMINI_API_URL}?key={api_key}"
    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {e.code}: {err_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Impossibile raggiungere Gemini: {e.reason}") from e

    data = json.loads(raw)

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Risposta Gemini inattesa: {data}") from e

    # Strip accidental markdown fences
    if text.startswith("```"):
        lines = text.splitlines()
        end   = -1 if lines[-1].strip() == "```" else len(lines)
        text  = "\n".join(lines[1:end])

    return text
