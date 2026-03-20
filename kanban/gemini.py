"""
KanFlow – Gemini AI integration
Calls the Gemini REST API using Python's built-in urllib (no extra deps).

Usage:
    Set the GOOGLE_API_KEY environment variable before running the app:
        export GOOGLE_API_KEY="your-key-here"          # Linux / macOS
        set GOOGLE_API_KEY=your-key-here               # Windows CMD
"""

import os
import json
import urllib.request
import urllib.error

# ── Configuration ─────────────────────────────────────────────────────────────

GEMINI_MODEL   = "gemini-2.5-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
Sei un assistente per la gestione di progetti che analizza appunti grezzi e li
trasforma in task strutturati per una board Kanban.

REGOLE ASSOLUTE:
1. Rispondi ESCLUSIVAMENTE con un array JSON valido, senza testo aggiuntivo.
2. Non usare blocchi markdown (no ```json).
3. Ogni elemento dell'array deve avere esattamente questi campi:
   - "title"       : stringa breve (max 100 caratteri), il titolo della task
   - "description" : stringa (può essere vuota "") con dettagli aggiuntivi
   - "status"      : uno di "todo", "in_progress", "done"
4. Inferisci lo status dal contesto:
   - "fatto", "completato", "✓", "done" → "done"
   - "in corso", "sto lavorando", "WIP" → "in_progress"
   - tutto il resto                     → "todo"
5. Suddividi azioni composte in task atomiche separate.
6. Ignora testo generico che non rappresenta un'azione concreta.
7. Se non trovi nessuna task, restituisci un array vuoto [].
"""

# ── Main function ─────────────────────────────────────────────────────────────

def extract_tasks_from_notes(notes_text: str) -> list[dict]:
    """
    Send raw notes to Gemini and get back a list of task dicts.

    Args:
        notes_text: Free-form text pasted by the user.

    Returns:
        List of dicts with keys: title, description, status.
        Empty list on failure (errors are raised to the caller).

    Raises:
        RuntimeError: API key missing, network error, or unexpected response.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY non trovata. "
            "Impostala come variabile d'ambiente prima di avviare l'app."
        )

    # ── Build request payload ─────────────────────────────────────────────────
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            f"Analizza questi appunti ed estraì le task:\n\n"
                            f"{notes_text.strip()}"
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature":     0.2,   # low temperature → deterministic, structured
            "maxOutputTokens": 2048,
        },
    }

    url      = f"{GEMINI_API_URL}?key={api_key}"
    body     = json.dumps(payload).encode("utf-8")
    req      = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # ── HTTP call ─────────────────────────────────────────────────────────────
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Impossibile raggiungere Gemini: {e.reason}") from e

    # ── Parse response ────────────────────────────────────────────────────────
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Risposta non valida da Gemini: {e}") from e

    # Navigate the Gemini response structure
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Struttura risposta Gemini inattesa: {data}") from e

    # Strip accidental markdown fences if the model adds them
    if text.startswith("```"):
        lines = text.splitlines()
        text  = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    # ── Parse JSON task list ──────────────────────────────────────────────────
    try:
        tasks = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"L'IA non ha restituito JSON valido.\nRisposta ricevuta:\n{text}"
        ) from e

    if not isinstance(tasks, list):
        raise RuntimeError("L'IA ha restituito un oggetto invece di un array.")

    # ── Sanitize each task ────────────────────────────────────────────────────
    valid_statuses = {"todo", "in_progress", "done"}
    result = []
    for item in tasks:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()[:200]
        if not title:
            continue
        result.append({
            "title":       title,
            "description": str(item.get("description") or "").strip(),
            "status":      item.get("status") if item.get("status") in valid_statuses else "todo",
        })

    return result
