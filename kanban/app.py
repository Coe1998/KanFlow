"""
KanFlow – Flask application
All routes + page rendering. Uses sqlite3-backed database.py (no ORM needed).
"""

from flask import Flask, render_template, request, jsonify, abort, send_file
import database as db
import gemini as ai
import git_utils as git
import doc_generator as docgen
import pdf_builder as pdfbuild
import io

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

with app.app_context():
    db.init_db()
    db.seed_demo_data()


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    projects = db.get_all_projects()
    return render_template("index.html", projects=projects)


@app.route("/project/<int:project_id>")
def board(project_id):
    project = db.get_project(project_id)
    if not project:
        abort(404)
    return render_template("board.html", project=project)


# ---------------------------------------------------------------------------
# Projects API
# ---------------------------------------------------------------------------

@app.route("/api/projects", methods=["GET"])
def api_get_projects():
    return jsonify(db.get_all_projects())


@app.route("/api/projects", methods=["POST"])
def api_create_project():
    data  = request.get_json(force=True)
    name  = (data.get("name") or "").strip()
    color = data.get("color", "#6C63FF")
    if not name:
        return jsonify({"error": "Project name is required"}), 400
    return jsonify(db.create_project(name, color)), 201


@app.route("/api/projects/<int:project_id>", methods=["GET"])
def api_get_project(project_id):
    project = db.get_project(project_id)
    if not project:
        abort(404)
    return jsonify(project)


@app.route("/api/projects/<int:project_id>", methods=["PUT"])
def api_update_project(project_id):
    if not db.get_project(project_id):
        abort(404)
    data  = request.get_json(force=True)
    name  = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Project name is required"}), 400
    updated = db.update_project(project_id, name=name, color=data.get("color"))
    return jsonify(updated)


@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def api_delete_project(project_id):
    if not db.get_project(project_id):
        abort(404)
    db.delete_project(project_id)
    return jsonify({"deleted": project_id})


# ---------------------------------------------------------------------------
# Labels API
# ---------------------------------------------------------------------------

@app.route("/api/projects/<int:project_id>/labels", methods=["GET"])
def api_get_labels(project_id):
    if not db.get_project(project_id):
        abort(404)
    return jsonify(db.get_project_labels(project_id))


@app.route("/api/projects/<int:project_id>/labels", methods=["POST"])
def api_create_label(project_id):
    if not db.get_project(project_id):
        abort(404)
    data  = request.get_json(force=True)
    name  = (data.get("name") or "").strip()[:40]
    color = data.get("color", "#6C63FF")
    if not name:
        return jsonify({"error": "Label name is required"}), 400
    return jsonify(db.create_label(project_id, name, color)), 201


@app.route("/api/labels/<int:label_id>", methods=["DELETE"])
def api_delete_label(label_id):
    db.delete_label(label_id)
    return jsonify({"deleted": label_id})


@app.route("/api/tasks/<int:task_id>/labels", methods=["PUT"])
def api_set_task_labels(task_id):
    task = db.get_task(task_id)
    if not task:
        abort(404)
    data      = request.get_json(force=True)
    label_ids = [int(i) for i in (data.get("label_ids") or [])]
    db.set_task_labels(task_id, label_ids)
    return jsonify(db.get_task(task_id))


# ---------------------------------------------------------------------------
# Git / file linking API
# ---------------------------------------------------------------------------

@app.route("/api/projects/<int:project_id>/git", methods=["GET"])
def api_get_git(project_id):
    """Return git_path + validation status for the project."""
    project = db.get_project(project_id)
    if not project:
        abort(404)
    git_path = project.get("git_path", "") or ""
    info     = git.validate_git_repo(git_path) if git_path else {"ok": False, "error": "Nessun percorso configurato"}
    return jsonify({"git_path": git_path, **info})


@app.route("/api/projects/<int:project_id>/git", methods=["PATCH"])
def api_set_git(project_id):
    """Set (or clear) the local git repo path for a project."""
    project = db.get_project(project_id)
    if not project:
        abort(404)
    data     = request.get_json(force=True)
    git_path = (data.get("git_path") or "").strip()

    if git_path:
        info = git.validate_git_repo(git_path)
        if not info["ok"]:
            return jsonify({"error": info["error"]}), 400

    db.update_project(project_id, git_path=git_path)
    updated  = db.get_project(project_id)
    val_info = git.validate_git_repo(git_path) if git_path else {"ok": False, "error": ""}
    return jsonify({"git_path": git_path, **val_info})


@app.route("/api/projects/<int:project_id>/git/browse")
def api_git_browse(project_id):
    """List files/dirs inside the linked repo (one level at a time)."""
    project  = db.get_project(project_id)
    if not project:
        abort(404)
    git_path = (project.get("git_path") or "").strip()
    if not git_path:
        return jsonify({"error": "Nessun repository collegato"}), 400

    subdir = request.args.get("path", "")
    tree   = git.get_file_tree(git_path, subdir)
    return jsonify(tree)


@app.route("/api/projects/<int:project_id>/git/status")
def api_git_status(project_id):
    """Return git status for all pinned files of this project."""
    project = db.get_project(project_id)
    if not project:
        abort(404)
    git_path = (project.get("git_path") or "").strip()
    if not git_path:
        return jsonify({})

    pinned = db.get_pinned_files(project_id)
    paths  = [f["rel_path"] for f in pinned]
    status = git.get_git_status(git_path, paths)
    return jsonify(status)


@app.route("/api/projects/<int:project_id>/git/commits")
def api_git_commits(project_id):
    """Return recent commits for a specific pinned file."""
    project = db.get_project(project_id)
    if not project:
        abort(404)
    git_path = (project.get("git_path") or "").strip()
    rel_path = request.args.get("path", "")
    if not git_path or not rel_path:
        return jsonify([])
    commits = git.get_recent_commits(git_path, rel_path)
    return jsonify(commits)


# Pinned files

@app.route("/api/projects/<int:project_id>/files", methods=["GET"])
def api_get_files(project_id):
    if not db.get_project(project_id):
        abort(404)
    return jsonify(db.get_pinned_files(project_id))


@app.route("/api/projects/<int:project_id>/files", methods=["POST"])
def api_pin_file(project_id):
    project = db.get_project(project_id)
    if not project:
        abort(404)
    data     = request.get_json(force=True)
    rel_path = (data.get("rel_path") or "").strip()
    note     = (data.get("note") or "").strip()
    is_dir   = bool(data.get("is_dir", False))
    if not rel_path:
        return jsonify({"error": "rel_path is required"}), 400
    return jsonify(db.pin_file(project_id, rel_path, note, is_dir)), 201


@app.route("/api/projects/<int:project_id>/files/<path:rel_path>", methods=["DELETE"])
def api_unpin_file(project_id, rel_path):
    if not db.get_project(project_id):
        abort(404)
    db.unpin_file(project_id, rel_path)
    return jsonify({"ok": True})


@app.route("/api/projects/<int:project_id>/files/<path:rel_path>", methods=["PATCH"])
def api_update_file_note(project_id, rel_path):
    if not db.get_project(project_id):
        abort(404)
    data = request.get_json(force=True)
    note = (data.get("note") or "").strip()
    updated = db.update_file_note(project_id, rel_path, note)
    if not updated:
        abort(404)
    return jsonify(updated)


@app.route("/api/projects/<int:project_id>/notes", methods=["GET"])
def api_get_notes(project_id):
    if not db.get_project(project_id):
        abort(404)
    return jsonify({"notes": db.get_project_notes(project_id)})


@app.route("/api/projects/<int:project_id>/notes", methods=["PATCH"])
def api_set_notes(project_id):
    if not db.get_project(project_id):
        abort(404)
    data  = request.get_json(force=True)
    notes = data.get("notes", "")
    if len(notes) > 50_000:
        return jsonify({"error": "Note troppo lunghe (max 50 000 caratteri)"}), 400
    saved = db.set_project_notes(project_id, notes)
    return jsonify({"notes": saved})


# ---------------------------------------------------------------------------
# AI extraction endpoint
# ---------------------------------------------------------------------------

@app.route("/api/projects/<int:project_id>/reorder", methods=["POST"])
def api_reorder_tasks(project_id):
    """
    Persist the new card order within a single column.
    Body: { "status": "todo", "order": [id, id, id, …] }
    """
    if not db.get_project(project_id):
        abort(404)
    data   = request.get_json(force=True)
    status = data.get("status", "")
    order  = data.get("order", [])

    if status not in ("todo", "in_progress", "done"):
        return jsonify({"error": "Invalid status"}), 400
    if not isinstance(order, list):
        return jsonify({"error": "order must be a list"}), 400

    db.reorder_tasks(project_id, status, [int(i) for i in order])
    return jsonify({"ok": True})


@app.route("/api/projects/<int:project_id>/generate-docs", methods=["POST"])
def api_generate_docs(project_id):
    """
    Gather all project context, call Gemini, render a styled PDF and return it
    as an inline download.
    """
    project = db.get_project(project_id)
    if not project:
        abort(404)

    try:
        # 1. Generate Markdown documentation via Gemini
        markdown = docgen.generate_project_docs(project_id)

        # 2. Gather task stats for the cover page
        tasks = db.get_tasks(project_id)
        stats = {
            "done":        sum(1 for t in tasks if t["status"] == "done"),
            "in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
            "todo":        sum(1 for t in tasks if t["status"] == "todo"),
        }

        # 3. Render PDF
        pdf_bytes = pdfbuild.markdown_to_pdf(markdown, project["name"], stats)

        # 4. Serve as download
        buf      = io.BytesIO(pdf_bytes)
        filename = project["name"].replace(" ", "_").replace("/", "-") + "_docs.pdf"
        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        return jsonify({"error": f"Errore generazione PDF: {e}"}), 500


@app.route("/api/projects/<int:project_id>/extract-tasks", methods=["POST"])
def api_extract_tasks(project_id):
    """
    Send raw notes to Gemini; return structured task list WITHOUT persisting.
    The client shows a preview and calls the normal create endpoint for each
    confirmed task.
    """
    if not db.get_project(project_id):
        abort(404)

    data  = request.get_json(force=True)
    notes = (data.get("notes") or "").strip()

    if not notes:
        return jsonify({"error": "Nessun testo fornito"}), 400
    if len(notes) > 10_000:
        return jsonify({"error": "Testo troppo lungo (max 10 000 caratteri)"}), 400

    try:
        tasks = ai.extract_tasks_from_notes(notes)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502

    return jsonify({"tasks": tasks})


# ---------------------------------------------------------------------------
# Tasks API
# ---------------------------------------------------------------------------

@app.route("/api/projects/<int:project_id>/tasks", methods=["GET"])
def api_get_tasks(project_id):
    if not db.get_project(project_id):
        abort(404)
    return jsonify(db.get_tasks(project_id))


@app.route("/api/projects/<int:project_id>/tasks", methods=["POST"])
def api_create_task(project_id):
    if not db.get_project(project_id):
        abort(404)
    data        = request.get_json(force=True)
    title       = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    status      = data.get("status", "todo")
    if not title:
        return jsonify({"error": "Task title is required"}), 400
    if status not in ("todo", "in_progress", "done"):
        status = "todo"
    return jsonify(db.create_task(project_id, title, description, status)), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def api_update_task(task_id):
    task = db.get_task(task_id)
    if not task:
        abort(404)
    data   = request.get_json(force=True)
    kwargs = {}
    if "title" in data:
        title = data["title"].strip()
        if not title:
            return jsonify({"error": "Title cannot be empty"}), 400
        kwargs["title"] = title
    if "description" in data:
        kwargs["description"] = (data["description"] or "").strip()
    if "status" in data:
        if data["status"] not in ("todo", "in_progress", "done"):
            return jsonify({"error": "Invalid status"}), 400
        kwargs["status"] = data["status"]
    if "position" in data:
        kwargs["position"] = int(data["position"])
    return jsonify(db.update_task(task_id, **kwargs))


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    if not db.get_task(task_id):
        abort(404)
    db.delete_task(task_id)
    return jsonify({"deleted": task_id})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
