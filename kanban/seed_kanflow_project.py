"""
seed_kanflow_project.py
Inserisce il progetto "KanFlow – Dev Board" con tutti i task
sviluppati durante la sessione di oggi.

Esegui UNA sola volta:
    python seed_kanflow_project.py
"""

import sys
import os

# Assicuriamoci di importare database.py dalla stessa cartella
sys.path.insert(0, os.path.dirname(__file__))
import database as db

# ---------------------------------------------------------------------------
# Dati del progetto
# ---------------------------------------------------------------------------

PROJECT_NAME  = "KanFlow – Dev Board"
PROJECT_COLOR = "#43B89C"   # teal, per distinguerlo dagli altri

# Ogni task: (titolo, descrizione, status)
TASKS = [

    # ── DONE ────────────────────────────────────────────────────────────────

    ("Setup progetto Flask",
     "Struttura cartelle: /templates, /static/css, /static/js. Entry point app.py con factory create_app().",
     "done"),

    ("Database SQLite con sqlite3 built-in",
     "database.py con get_conn(), init_db(), tabelle projects e tasks. Nessuna dipendenza esterna oltre Flask.",
     "done"),

    ("Modello Project",
     "Tabella projects: id, name, color, notes, created_at. Helper CRUD: get_all_projects, create_project, update_project, delete_project.",
     "done"),

    ("Modello Task",
     "Tabella tasks: id, project_id (FK cascade), title, description, status, position, created_at.",
     "done"),

    ("REST API – Progetti",
     "GET /api/projects, POST /api/projects, PUT /api/projects/<id>, DELETE /api/projects/<id>, GET /api/projects/<id>.",
     "done"),

    ("REST API – Task",
     "GET /api/projects/<id>/tasks, POST /api/projects/<id>/tasks, PUT /api/tasks/<id>, DELETE /api/tasks/<id>.",
     "done"),

    ("Pagina Home – lista progetti",
     "Grid responsive di project card con color bar, nome, contatore task e bottoni rename/delete.",
     "done"),

    ("Kanban board – layout 3 colonne",
     "Colonne TODO / IN PROGRESS / DONE con header badge colorati e contatore card per colonna.",
     "done"),

    ("Drag & drop tra colonne",
     "HTML5 DnD con placeholder animato, highlight colonna target, aggiornamento status via API al drop.",
     "done"),

    ("Modal Crea/Modifica Task",
     "Textarea per titolo e descrizione, status tab selector, salvataggio con Invio. Pulsante Delete in edit mode.",
     "done"),

    ("Modal Crea/Rinomina Progetto",
     "Input nome + 6 colour swatches. Riutilizzato per create e rename cambiando titolo e label del bottone.",
     "done"),

    ("Confirm modal per delete",
     "Modal di conferma riutilizzabile per delete progetto e delete task, con messaggio contestuale.",
     "done"),

    ("Toast notification",
     "Messaggio toast bottom-right con varianti success/error, auto-dismiss dopo 2.8 s.",
     "done"),

    ("Design system dark mode",
     "CSS custom properties per superfici, testi, accenti. Font Syne (display) + DM Sans (body). Scrollbar personalizzata.",
     "done"),

    ("Progress bar completamento progetto",
     "Query SQL con SUM(CASE WHEN status='done') per calcolare %, progress bar animata con shimmer. Stato verde+glow al 100%.",
     "done"),

    ("Refresh progress al ritorno dalla board",
     "refreshCardProgress() chiama GET /api/projects/<id> al DOMContentLoaded e aggiorna barra senza reload.",
     "done"),

    ("Integrazione Gemini AI – estrazione task",
     "gemini.py chiama gemini-2.5-flash via urllib (no deps). Endpoint POST /api/projects/<id>/extract-tasks restituisce preview senza salvare.",
     "done"),

    ("UI estrazione AI – modal 2 step",
     "Step 1: textarea appunti. Step 2: preview card selezionabili con checkbox, badge status inferito, select-all toggle.",
     "done"),

    ("Note di progetto – drawer laterale",
     "Slide-in drawer con textarea monospace, toolbar formattazione, auto-save debounced 3 s, Ctrl+S.",
     "done"),

    ("Markdown renderer custom",
     "Parser da zero: headings, **bold**, *italic*, `code`, fenced code blocks con label lingua e bottone copia, liste, blockquote, HR.",
     "done"),

    ("Migrazione DB safe per colonna notes",
     "PRAGMA table_info + ALTER TABLE ADD COLUMN per aggiornare DB esistenti senza perdere dati.",
     "done"),

    ("Bug fix: .hidden scomparso dal CSS",
     "La regola .hidden { display:none !important } era stata rimossa per errore durante una str_replace, causando la visualizzazione di tutti i modal all'avvio.",
     "done"),

    # ── IN PROGRESS ─────────────────────────────────────────────────────────

    ("Seed progetto KanFlow nel proprio board",
     "Script seed_kanflow_project.py che inserisce il dev board di KanFlow come primo progetto reale nell'app.",
     "in_progress"),

    # ── TODO ────────────────────────────────────────────────────────────────

    ("Responsive mobile completo",
     "Il drawer note e la board vanno ottimizzati per viewport < 480px. Testare drag & drop su touch.",
     "todo"),

    ("Ordinamento manuale task nella stessa colonna",
     "Drag & drop all'interno della stessa colonna con aggiornamento del campo position via API.",
     "todo"),

    ("Filtro / ricerca task",
     "Barra di ricerca nella board per filtrare card per testo. Highlight del termine cercato nelle card.",
     "todo"),

    ("Etichette colorate per i task",
     "Tag personalizzabili per categoria (es. bug, feature, docs). Visibili come pillole sulle card.",
     "todo"),

    ("Data di scadenza per i task",
     "Campo due_date opzionale. Badge rosso sulla card se scaduto, giallo se in scadenza entro 2 giorni.",
     "todo"),

    ("Export board in Markdown / JSON",
     "Bottone nella board per scaricare tutti i task come file .md strutturato o .json per backup.",
     "todo"),

]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    db.init_db()

    # Evita duplicati se lo script viene rieseguito
    existing = [p["name"] for p in db.get_all_projects()]
    if PROJECT_NAME in existing:
        print(f"⚠️  Il progetto '{PROJECT_NAME}' esiste già. Script non eseguito.")
        print("   Elimina prima il progetto dall'app se vuoi ricrearlo.")
        return

    print(f"Creazione progetto '{PROJECT_NAME}'…")
    project = db.create_project(PROJECT_NAME, PROJECT_COLOR)
    pid = project["id"]

    counts = {"todo": 0, "in_progress": 0, "done": 0}
    for title, description, status in TASKS:
        db.create_task(pid, title, description, status)
        counts[status] += 1

    total = sum(counts.values())
    print(f"✓ {total} task inseriti:")
    print(f"  DONE        → {counts['done']}")
    print(f"  IN PROGRESS → {counts['in_progress']}")
    print(f"  TODO        → {counts['todo']}")
    print()
    print(f"Apri http://localhost:5000 e cerca il progetto '{PROJECT_NAME}'.")


if __name__ == "__main__":
    main()
