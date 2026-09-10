from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "products.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            company TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


def validate_client_form(form: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    name = form.get("name", "").strip()
    email = form.get("email", "").strip().lower()
    phone = form.get("phone", "").strip()
    company = form.get("company", "").strip()
    notes = form.get("notes", "").strip()

    errors: list[str] = []

    if not name:
        errors.append("El nombre es obligatorio.")

    if not email:
        errors.append("El correo electrónico es obligatorio.")
    elif "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        errors.append("El correo electrónico no es válido.")

    cleaned = {
        "name": name,
        "email": email,
        "phone": phone,
        "company": company,
        "notes": notes,
    }
    return cleaned, errors


@app.route("/")
def index() -> str:
    db = get_db()
    clients = db.execute(
        "SELECT id, name, email, phone, company, notes, created_at, updated_at "
        "FROM clients ORDER BY id DESC"
    ).fetchall()
    return render_template("index.html", clients=clients)


@app.route("/clients/new", methods=["GET", "POST"])
def create_client() -> str:
    if request.method == "POST":
        data, errors = validate_client_form(request.form.to_dict())
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("form.html", client=data, mode="create")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO clients (name, email, phone, company, notes) VALUES (?, ?, ?, ?, ?)",
                (
                    data["name"],
                    data["email"],
                    data["phone"],
                    data["company"],
                    data["notes"],
                ),
            )
        except sqlite3.IntegrityError:
            flash("El correo electrónico ya existe. Usa un correo único.", "error")
            return render_template("form.html", client=data, mode="create")

        db.commit()
        flash("Cliente creado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", client={}, mode="create")


@app.route("/clients/<int:client_id>")
def client_detail(client_id: int) -> str:
    db = get_db()
    client = db.execute(
        "SELECT id, name, email, phone, company, notes, created_at, updated_at FROM clients WHERE id = ?",
        (client_id,),
    ).fetchone()

    if client is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("index"))

    return render_template("detail.html", client=client)


@app.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
def edit_client(client_id: int) -> str:
    db = get_db()
    client = db.execute(
        "SELECT id, name, email, phone, company, notes FROM clients WHERE id = ?",
        (client_id,),
    ).fetchone()

    if client is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        data, errors = validate_client_form(request.form.to_dict())
        if errors:
            for error in errors:
                flash(error, "error")
            data["id"] = client_id
            return render_template("form.html", client=data, mode="edit")

        try:
            db.execute(
                """
                UPDATE clients
                SET name = ?, email = ?, phone = ?, company = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    data["name"],
                    data["email"],
                    data["phone"],
                    data["company"],
                    data["notes"],
                    client_id,
                ),
            )
        except sqlite3.IntegrityError:
            flash("El correo electrónico ya existe. Usa un correo único.", "error")
            data["id"] = client_id
            return render_template("form.html", client=data, mode="edit")

        db.commit()
        flash("Cliente actualizado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", client=client, mode="edit")


@app.route("/clients/<int:client_id>/delete", methods=["POST"])
def delete_client(client_id: int) -> str:
    db = get_db()
    deleted = db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    db.commit()

    if deleted.rowcount == 0:
        flash("Cliente no encontrado.", "error")
    else:
        flash("Cliente eliminado correctamente.", "success")

    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
