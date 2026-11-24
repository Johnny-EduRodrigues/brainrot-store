from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import escape
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import unicodedata

from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

from services.database import DATABASE_PATH, get_connection, initialize_schema
from services.seed import popular_banco


ROOT = Path(__file__).resolve().parents[1]
FRONT_ROOT = ROOT / "front"


def brainrot_json(row):
    return {
        "slug": row["slug"],
        "name": row["name"],
        "description": row["description"],
        "price_cents": row["price_cents"],
        "stock": row["stock"],
        "image_path": row["image_path"],
        "category": row["category"],
        "rarity": row["rarity"],
        "rarity_color": row["rarity_color"],
    }


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug[:70].rstrip("-")


def current_user(connection):
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return connection.execute(
        "SELECT id, username, role FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


def user_json(user):
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


def initial_app_secret(database_path):
    configured_secret = os.environ.get("SECRET_KEY")
    if configured_secret:
        return configured_secret
    with get_connection(database_path) as connection:
        row = connection.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = 'flask-secret-key'"
        ).fetchone()
        if row:
            return row["setting_value"]
        secret = secrets.token_urlsafe(48)
        connection.execute(
            "INSERT INTO app_settings (setting_key, setting_value) VALUES ('flask-secret-key', ?)",
            (secret,),
        )
        return secret


def ensure_initial_admin(database_path):
    username = os.environ.get("ADMIN_USERNAME", "admin").strip()
    password = os.environ.get("ADMIN_PASSWORD")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username):
        raise ValueError("ADMIN_USERNAME deve ter de 3 a 30 caracteres válidos.")
    with get_connection(database_path) as connection:
        existing = connection.execute(
            "SELECT id, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if existing:
            if existing["role"] != "admin":
                raise ValueError(f"O usuário configurado para admin ({username}) já existe como conta comum.")
            if password:
                if len(password) < 8:
                    raise ValueError("ADMIN_PASSWORD deve ter pelo menos 8 caracteres.")
                connection.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (generate_password_hash(password), existing["id"]),
                )
            return
        if password and len(password) < 8:
            raise ValueError("ADMIN_PASSWORD deve ter pelo menos 8 caracteres.")
        if not password:
            password = secrets.token_urlsafe(18)
            print(f"Admin inicial criado — usuário: {username} | senha: {password}")
        connection.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
            (username, generate_password_hash(password)),
        )


def create_placeholder_image(path, name, rarity_color):
    markup = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 360">
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="{escape(rarity_color)}"/><stop offset="1" stop-color="#111827"/></linearGradient></defs>
<rect width="320" height="360" rx="24" fill="url(#bg)"/>
<circle cx="160" cy="145" r="86" fill="#ffffff" fill-opacity=".12" stroke="#ffffff" stroke-opacity=".4" stroke-width="2"/>
<text x="160" y="177" text-anchor="middle" font-size="82" font-family="sans-serif">🧠</text>
<rect x="22" y="264" width="276" height="66" rx="14" fill="#101827" fill-opacity=".75"/>
<text x="160" y="303" text-anchor="middle" fill="#ffffff" font-size="17" font-family="sans-serif">{escape(name)}</text>
</svg>"""
    path.write_text(markup, encoding="utf-8")


def create_app(database_path=DATABASE_PATH):
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = database_path
    app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    initialize_schema(database_path)
    app.config["SECRET_KEY"] = initial_app_secret(database_path)
    popular_banco(database_path)
    ensure_initial_admin(database_path)

    def csrf_error():
        expected = session.get("csrf_token", "")
        supplied = request.headers.get("X-CSRF-Token", "")
        if not expected or not hmac.compare_digest(expected, supplied):
            return jsonify({"error": "Sessão expirada. Atualize a página e tente novamente."}), 400
        return None

    @app.get("/")
    def home():
        return send_from_directory(FRONT_ROOT, "index.html")

    @app.get("/styles.css")
    def styles():
        return send_from_directory(FRONT_ROOT, "styles.css")

    @app.get("/app.js")
    def script():
        return send_from_directory(FRONT_ROOT, "app.js")

    @app.get("/favicon.png")
    def favicon():
        return send_from_directory(FRONT_ROOT / "public", "favicon.png")

    @app.get("/public/brainrots/<path:filename>")
    def brainrot_image(filename):
        return send_from_directory(FRONT_ROOT / "public" / "brainrots", filename)

    @app.get("/api/auth/csrf")
    def get_csrf_token():
        session.setdefault("csrf_token", secrets.token_urlsafe(32))
        return jsonify({"csrf_token": session["csrf_token"]})

    @app.get("/api/auth/me")
    def get_current_user():
        session.setdefault("csrf_token", secrets.token_urlsafe(32))
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            user = current_user(connection)
        return jsonify({
            "user": user_json(user) if user else None,
            "csrf_token": session["csrf_token"],
        })

    @app.post("/api/auth/register")
    def register():
        csrf = csrf_error()
        if csrf:
            return csrf
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Dados de cadastro inválidos."}), 400
        username = payload.get("username", "")
        password = payload.get("password", "")
        if not isinstance(username, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username.strip()):
            return jsonify({"error": "Use um usuário de 3 a 30 caracteres (letras, números, ponto, hífen ou _)."}), 400
        username = username.strip()
        if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
            return jsonify({"error": "A senha deve ter entre 8 e 128 caracteres."}), 400
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            try:
                cursor = connection.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
                    (username, generate_password_hash(password)),
                )
            except sqlite3.IntegrityError:
                return jsonify({"error": "Esse nome de usuário já está em uso."}), 409
            user = connection.execute(
                "SELECT id, username, role FROM users WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        session.clear()
        session["user_id"] = user["id"]
        session["csrf_token"] = secrets.token_urlsafe(32)
        return jsonify({"user": user_json(user), "csrf_token": session["csrf_token"]}), 201

    @app.post("/api/auth/login")
    def login():
        csrf = csrf_error()
        if csrf:
            return csrf
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Usuário ou senha inválidos."}), 401
        username = payload.get("username", "")
        password = payload.get("password", "")
        if not isinstance(username, str) or not isinstance(password, str):
            return jsonify({"error": "Usuário ou senha inválidos."}), 401
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            row = connection.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()
        if row is None or not check_password_hash(row["password_hash"], password):
            return jsonify({"error": "Usuário ou senha inválidos."}), 401
        session.clear()
        session["user_id"] = row["id"]
        session["csrf_token"] = secrets.token_urlsafe(32)
        user = {"id": row["id"], "username": row["username"], "role": row["role"]}
        return jsonify({"user": user, "csrf_token": session["csrf_token"]})

    @app.post("/api/auth/logout")
    def logout():
        csrf = csrf_error()
        if csrf:
            return csrf
        session.clear()
        session["csrf_token"] = secrets.token_urlsafe(32)
        return jsonify({"message": "Sessão encerrada.", "csrf_token": session["csrf_token"]})

    @app.get("/api/catalog-options")
    def catalog_options():
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            categories = connection.execute("SELECT id, name FROM categories ORDER BY name").fetchall()
            rarities = connection.execute("SELECT id, name, color FROM rarities ORDER BY id").fetchall()
        return jsonify({
            "categories": [dict(row) for row in categories],
            "rarities": [dict(row) for row in rarities],
        })

    @app.get("/api/brainrots")
    def list_brainrots():
        search = request.args.get("q", "").strip()
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            rows = connection.execute(
                """
                SELECT b.*, c.name AS category, r.name AS rarity, r.color AS rarity_color
                FROM brainrots b
                JOIN categories c ON c.id = b.category_id
                JOIN rarities r ON r.id = b.rarity_id
                WHERE (? = '' OR b.name LIKE ? OR b.description LIKE ?)
                ORDER BY b.id
                """,
                (search, f"%{search}%", f"%{search}%"),
            ).fetchall()
        return jsonify([brainrot_json(row) for row in rows])

    @app.get("/api/brainrots/<slug>")
    def get_brainrot(slug):
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            row = connection.execute(
                """
                SELECT b.*, c.name AS category, r.name AS rarity, r.color AS rarity_color
                FROM brainrots b
                JOIN categories c ON c.id = b.category_id
                JOIN rarities r ON r.id = b.rarity_id
                WHERE b.slug = ?
                """,
                (slug,),
            ).fetchone()
        if row is None:
            return jsonify({"error": "Brainrot não encontrado."}), 404
        return jsonify(brainrot_json(row))

    @app.post("/api/brainrots")
    def create_brainrot():
        csrf = csrf_error()
        if csrf:
            return csrf
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            user = current_user(connection)
            if user is None:
                return jsonify({"error": "Faça login para continuar."}), 401
            if user["role"] != "admin":
                return jsonify({"error": "Apenas administradores podem cadastrar Brainrots."}), 403
        image = request.files.get("image")
        image_bytes = image.read(5 * 1024 * 1024 + 1) if image and image.filename else None
        extension = Path(image.filename).suffix.lower() if image and image.filename else ""
        if image_bytes is not None:
            valid_signatures = {
                ".png": image_bytes.startswith(b"\x89PNG\r\n\x1a\n"),
                ".jpg": image_bytes.startswith(b"\xff\xd8\xff"),
                ".jpeg": image_bytes.startswith(b"\xff\xd8\xff"),
                ".webp": image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP",
            }
            if len(image_bytes) > 5 * 1024 * 1024 or not valid_signatures.get(extension, False):
                return jsonify({"error": "Envie uma imagem PNG, JPG ou WebP válida, de até 5 MB."}), 400

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        try:
            price = Decimal(request.form.get("price", "")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            stock = int(request.form.get("stock", ""))
            category_id = int(request.form.get("category_id", ""))
            rarity_id = int(request.form.get("rarity_id", ""))
        except (InvalidOperation, ValueError):
            return jsonify({"error": "Preço, estoque, categoria ou raridade inválidos."}), 400
        if not name or len(name) > 80 or not description or len(description) > 600:
            return jsonify({"error": "Informe nome (até 80 caracteres) e descrição (até 600 caracteres)."}), 400
        if not price.is_finite() or price < 0 or price > Decimal("99999999"):
            return jsonify({"error": "Informe um preço válido."}), 400
        if stock < 0 or stock > 1_000_000:
            return jsonify({"error": "O estoque deve estar entre 0 e 1.000.000."}), 400

        with get_connection(app.config["DATABASE_PATH"]) as connection:
            user = current_user(connection)
            if user is None:
                return jsonify({"error": "Faça login para continuar."}), 401
            if user["role"] != "admin":
                return jsonify({"error": "Apenas administradores podem cadastrar Brainrots."}), 403
            category = connection.execute(
                "SELECT id FROM categories WHERE id = ?",
                (category_id,),
            ).fetchone()
            rarity = connection.execute(
                "SELECT id, color FROM rarities WHERE id = ?",
                (rarity_id,),
            ).fetchone()
            if category is None or rarity is None:
                return jsonify({"error": "Selecione uma categoria e raridade existentes."}), 400

            base_slug = slugify(name) or f"brainrot-{secrets.token_hex(4)}"
            slug = base_slug
            suffix = 2
            image_directory = FRONT_ROOT / "public" / "brainrots"
            while connection.execute(
                "SELECT 1 FROM brainrots WHERE slug = ?",
                (slug,),
            ).fetchone() or (image_directory / f"{slug}{extension or '.svg'}").exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            extension = extension or ".svg"
            image_file = image_directory / f"{slug}{extension}"
            image_path = f"/public/brainrots/{slug}{extension}"
            try:
                if image_bytes is None:
                    create_placeholder_image(image_file, name, rarity["color"])
                else:
                    image_file.write_bytes(image_bytes)
                cursor = connection.execute(
                    """
                    INSERT INTO brainrots
                        (slug, name, description, price_cents, stock, image_path, category_id, rarity_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        slug,
                        name,
                        description,
                        int(price * 100),
                        stock,
                        image_path,
                        category_id,
                        rarity_id,
                    ),
                )
            except sqlite3.IntegrityError:
                image_file.unlink(missing_ok=True)
                return jsonify({"error": "Não foi possível cadastrar esse Brainrot."}), 409
            except OSError:
                image_file.unlink(missing_ok=True)
                raise
            row = connection.execute(
                """
                SELECT b.*, c.name AS category, r.name AS rarity, r.color AS rarity_color
                FROM brainrots b
                JOIN categories c ON c.id = b.category_id
                JOIN rarities r ON r.id = b.rarity_id
                WHERE b.id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
        return jsonify(brainrot_json(row)), 201

    @app.post("/popular-banco")
    def populate_database():
        popular_banco(app.config["DATABASE_PATH"])
        return jsonify({"message": "Banco populado com sucesso.", "total": 22})

    @app.get("/api/orders")
    def list_orders():
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            user = current_user(connection)
            if user is None:
                return jsonify({"error": "Entre na sua conta para ver os pedidos."}), 401
            rows = connection.execute(
                """
                SELECT id, created_at, total_cents
                FROM orders
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user["id"],),
            ).fetchall()
            orders = []
            for order in rows:
                items = connection.execute(
                    """
                    SELECT name, price_cents, quantity, image_path
                    FROM order_items
                    WHERE order_id = ?
                    """,
                    (order["id"],),
                ).fetchall()
                orders.append({
                    "id": order["id"],
                    "created_at": order["created_at"],
                    "total_cents": order["total_cents"],
                    "items": [dict(item) for item in items],
                })
        return jsonify(orders)

    @app.post("/api/orders")
    def create_order():
        csrf = csrf_error()
        if csrf:
            return csrf
        payload = request.get_json(silent=True) or {}
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            return jsonify({"error": "Adicione ao menos um produto ao carrinho."}), 400

        quantities = {}
        for item in items:
            if not isinstance(item, dict):
                return jsonify({"error": "Item de pedido inválido."}), 400
            slug = item.get("slug")
            quantity = item.get("quantity")
            if not isinstance(slug, str) or not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
                return jsonify({"error": "Produto ou quantidade inválida."}), 400
            quantities[slug] = quantities.get(slug, 0) + quantity

        order_items = []
        total_cents = 0
        with get_connection(app.config["DATABASE_PATH"]) as connection:
            user = current_user(connection)
            if user is None:
                return jsonify({"error": "Entre na sua conta para finalizar a compra."}), 401
            try:
                connection.execute("BEGIN IMMEDIATE")
                for slug, quantity in quantities.items():
                    row = connection.execute(
                        "SELECT id, slug, name, price_cents, stock, image_path FROM brainrots WHERE slug = ?",
                        (slug,),
                    ).fetchone()
                    if row is None:
                        connection.rollback()
                        return jsonify({"error": f"Produto não encontrado: {slug}."}), 404
                    if row["stock"] < quantity:
                        connection.rollback()
                        return jsonify({"error": f"Estoque insuficiente para {row['name']}."}), 409
                    total_cents += row["price_cents"] * quantity
                    order_items.append((row, quantity))

                order_id = connection.execute(
                    "INSERT INTO orders (total_cents, user_id) VALUES (?, ?)",
                    (total_cents, user["id"]),
                ).lastrowid
                for row, quantity in order_items:
                    connection.execute(
                        "UPDATE brainrots SET stock = stock - ? WHERE id = ?",
                        (quantity, row["id"]),
                    )
                    connection.execute(
                        """
                        INSERT INTO order_items (order_id, brainrot_id, name, price_cents, quantity, image_path)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (order_id, row["id"], row["name"], row["price_cents"], quantity, row["image_path"]),
                    )
            except sqlite3.Error:
                connection.rollback()
                raise

        return jsonify({
            "id": order_id,
            "total_cents": total_cents,
            "items": [
                {
                    "name": row["name"],
                    "price_cents": row["price_cents"],
                    "quantity": quantity,
                    "image_path": row["image_path"],
                }
                for row, quantity in order_items
            ],
        }), 201

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
