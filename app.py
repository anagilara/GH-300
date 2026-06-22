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
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            price REAL NOT NULL CHECK(price >= 0),
            tax REAL NOT NULL DEFAULT 0 CHECK(tax >= 0 AND tax <= 100),
            stock INTEGER NOT NULL CHECK(stock >= 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Migra una base existente creada antes de incluir SKU e impuesto.
    columns = {row[1] for row in db.execute("PRAGMA table_info(products)").fetchall()}
    if "sku" not in columns:
        db.execute("ALTER TABLE products ADD COLUMN sku TEXT")
    if "tax" not in columns:
        db.execute("ALTER TABLE products ADD COLUMN tax REAL NOT NULL DEFAULT 0")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku ON products(sku)")

    db.commit()
    db.close()


def validate_product_form(form: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    sku = form.get("sku", "").strip().upper()
    name = form.get("name", "").strip()
    description = form.get("description", "").strip()
    category = form.get("category", "").strip()
    price_raw = form.get("price", "").strip()
    tax_raw = form.get("tax", "").strip()
    stock_raw = form.get("stock", "").strip()

    errors: list[str] = []

    if not sku:
        errors.append("El SKU es obligatorio.")

    if not name:
        errors.append("El nombre es obligatorio.")

    try:
        price = float(price_raw)
        if price < 0:
            errors.append("El precio debe ser mayor o igual a 0.")
    except ValueError:
        errors.append("El precio debe ser un número válido.")
        price = 0.0

    try:
        tax = float(tax_raw)
        if tax < 0 or tax > 100:
            errors.append("El impuesto debe estar entre 0 y 100.")
    except ValueError:
        errors.append("El impuesto debe ser un número válido.")
        tax = 0.0

    try:
        stock = int(stock_raw)
        if stock < 0:
            errors.append("El stock debe ser mayor o igual a 0.")
    except ValueError:
        errors.append("El stock debe ser un número entero válido.")
        stock = 0

    cleaned = {
        "sku": sku,
        "name": name,
        "description": description,
        "category": category,
        "price": price,
        "tax": tax,
        "stock": stock,
    }
    return cleaned, errors


@app.route("/")
def index() -> str:
    db = get_db()
    products = db.execute(
        "SELECT id, sku, name, description, category, price, tax, stock, created_at, updated_at "
        "FROM products ORDER BY id DESC"
    ).fetchall()
    return render_template("index.html", products=products)


@app.route("/products/new", methods=["GET", "POST"])
def create_product() -> str:
    if request.method == "POST":
        data, errors = validate_product_form(request.form.to_dict())
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("form.html", product=data, mode="create")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO products (sku, name, description, category, price, tax, stock) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    data["sku"],
                    data["name"],
                    data["description"],
                    data["category"],
                    data["price"],
                    data["tax"],
                    data["stock"],
                ),
            )
        except sqlite3.IntegrityError:
            flash("El SKU ya existe. Usa un SKU único.", "error")
            return render_template("form.html", product=data, mode="create")

        db.commit()
        flash("Producto creado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", product={}, mode="create")


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id: int) -> str:
    db = get_db()
    product = db.execute(
        "SELECT id, sku, name, description, category, price, tax, stock FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if product is None:
        flash("Producto no encontrado.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        data, errors = validate_product_form(request.form.to_dict())
        if errors:
            for error in errors:
                flash(error, "error")
            data["id"] = product_id
            return render_template("form.html", product=data, mode="edit")

        try:
            db.execute(
                """
                UPDATE products
                SET sku = ?, name = ?, description = ?, category = ?, price = ?, tax = ?, stock = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    data["sku"],
                    data["name"],
                    data["description"],
                    data["category"],
                    data["price"],
                    data["tax"],
                    data["stock"],
                    product_id,
                ),
            )
        except sqlite3.IntegrityError:
            flash("El SKU ya existe. Usa un SKU único.", "error")
            data["id"] = product_id
            return render_template("form.html", product=data, mode="edit")

        db.commit()
        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", product=product, mode="edit")


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id: int) -> str:
    db = get_db()
    deleted = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()

    if deleted.rowcount == 0:
        flash("Producto no encontrado.", "error")
    else:
        flash("Producto eliminado correctamente.", "success")

    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
