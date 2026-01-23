import os
import uuid
from decimal import Decimal, InvalidOperation

from io import BytesIO
from flask import send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from models import Base, User, PriceItem
from db_init import init_db, db_url_from_env

load_dotenv()

UPLOAD_DIR = os.path.join("static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

os.makedirs(UPLOAD_DIR, exist_ok=True)

engine = create_engine(db_url_from_env(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def current_user(db):
    uid = session.get("user_id")
    if not uid:
        return None
    return db.get(User, uid)

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def avatar_url(user: User) -> str:
    if user.avatar_filename:
        return url_for("static", filename=f"uploads/{user.avatar_filename}")
    return url_for("static", filename="uploads/default-avatar.svg")



@app.get("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        db = SessionLocal()
        try:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Identifiants invalides.", "error")
                return render_template("login.html")

            session["user_id"] = user.id
            return redirect(url_for("home"))
        finally:
            db.close()

    return render_template("login.html")

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/home")
@login_required
def home():
    db = SessionLocal()
    try:
        user = current_user(db)
        return render_template("home.html", user=user, avatar=avatar_url(user))
    finally:
        db.close()

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = SessionLocal()
    try:
        user = current_user(db)

        if request.method == "POST":
            # champs texte
            user.first_name = (request.form.get("first_name") or "").strip()
            user.last_name = (request.form.get("last_name") or "").strip()
            new_email = (request.form.get("email") or "").strip().lower()

            # email unique
            if new_email and new_email != user.email:
                exists = db.execute(select(User).where(User.email == new_email)).scalar_one_or_none()
                if exists:
                    flash("Cet email est déjà utilisé.", "error")
                    return render_template("profile.html", user=user, avatar=avatar_url(user))
                user.email = new_email

            # mdp (optionnel)
            new_pwd = request.form.get("new_password") or ""
            new_pwd2 = request.form.get("new_password_confirm") or ""
            if new_pwd or new_pwd2:
                if new_pwd != new_pwd2:
                    flash("Les mots de passe ne correspondent pas.", "error")
                    return render_template("profile.html", user=user, avatar=avatar_url(user))
                if len(new_pwd) < 8:
                    flash("Mot de passe trop court (min 8).", "error")
                    return render_template("profile.html", user=user, avatar=avatar_url(user))
                user.password_hash = generate_password_hash(new_pwd)

            # avatar (optionnel)
            file = request.files.get("avatar")
            if file and file.filename:
                ext = file.filename.rsplit(".", 1)[-1].lower()
                if ext not in ALLOWED_EXT:
                    flash("Format avatar non supporté (png/jpg/jpeg/webp).", "error")
                    return render_template("profile.html", user=user, avatar=avatar_url(user))

                safe = secure_filename(file.filename)
                unique = f"{uuid.uuid4().hex}_{safe}"
                path = os.path.join(UPLOAD_DIR, unique)
                file.save(path)

                # option : supprimer l'ancien fichier si présent
                if user.avatar_filename:
                    old = os.path.join(UPLOAD_DIR, user.avatar_filename)
                    if os.path.exists(old):
                        try:
                            os.remove(old)
                        except OSError:
                            pass

                user.avatar_filename = unique

            db.commit()
            flash("Profil mis à jour.", "ok")
            return redirect(url_for("profile"))

        return render_template("profile.html", user=user, avatar=avatar_url(user))
    finally:
        db.close()

@app.get("/prices")
@login_required
def prices_page():
    db = SessionLocal()
    try:
        user = current_user(db)
        items = db.execute(
            select(PriceItem)
            .where(PriceItem.group_id == user.group_id)
            .order_by(PriceItem.created_at.desc())
        ).scalars().all()
        return render_template("prices.html", user=user, avatar=avatar_url(user), items=items)
    finally:
        db.close()

@app.post("/prices/create")
@login_required
def prices_create():
    label = (request.form.get("label") or "").strip()
    price_raw = (request.form.get("price") or "").strip()

    if not label:
        flash("Libellé requis.", "error")
        return redirect(url_for("prices_page"))

    try:
        price = Decimal(price_raw)
    except InvalidOperation:
        flash("Prix invalide.", "error")
        return redirect(url_for("prices_page"))

    if price < 0:
        flash("Prix doit être >= 0.", "error")
        return redirect(url_for("prices_page"))

    db = SessionLocal()
    try:
        user = current_user(db)
        db.add(PriceItem(
            label=label,
            price=price,
            group_id=user.group_id,
            created_by_user_id=user.id
        ))
        db.commit()
        flash("Prix ajouté.", "ok")
        return redirect(url_for("prices_page"))
    finally:
        db.close()

@app.delete("/prices/<int:item_id>")
@login_required
def prices_delete(item_id: int):
    db = SessionLocal()
    try:
        user = current_user(db)
        item = db.get(PriceItem, item_id)
        if not item or item.group_id != user.group_id:
            return jsonify({"ok": False, "error": "Not found"}), 404


        db.delete(item)
        db.commit()
        return jsonify({"ok": True})
    finally:
        db.close()

def ensure_default_avatar_file():
    default_svg = os.path.join(UPLOAD_DIR, "default-avatar.svg")
    if not os.path.exists(default_svg):
        with open(default_svg, "w", encoding="utf-8") as f:
            f.write("""<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#7c3aed"/>
      <stop offset="1" stop-color="#06b6d4"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="56" fill="url(#g)"/>
  <circle cx="128" cy="104" r="44" fill="rgba(255,255,255,0.85)"/>
  <path d="M52 220c10-44 46-72 76-72s66 28 76 72" fill="rgba(255,255,255,0.85)"/>
</svg>""")

@app.get("/prices/invoice.pdf")
@login_required
def prices_invoice_pdf():
    db = SessionLocal()
    try:
        user = current_user(db)

        items = db.execute(
            select(PriceItem)
            .where(PriceItem.group_id == user.group_id)
            .order_by(PriceItem.created_at.desc())
        ).scalars().all()

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Header
        y = height - 60
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Facture - Liste des prix")
        y -= 22

        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Client: {user.first_name} {user.last_name} ({user.email})")
        y -= 14
        c.drawString(50, y, f"Groupe ID: {user.group_id}")
        y -= 22

        # Table header
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Libellé")
        c.drawRightString(width - 50, y, "Prix (€)")
        y -= 12
        c.line(50, y, width - 50, y)
        y -= 18

        # Rows
        total = Decimal("0.00")
        c.setFont("Helvetica", 11)

        for it in items:
            # nouvelle page si besoin
            if y < 80:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica-Bold", 11)
                c.drawString(50, y, "Libellé")
                c.drawRightString(width - 50, y, "Prix (€)")
                y -= 12
                c.line(50, y, width - 50, y)
                y -= 18
                c.setFont("Helvetica", 11)

            label = (it.label or "")[:80]
            price = Decimal(it.price)
            total += price

            c.drawString(50, y, label)
            c.drawRightString(width - 50, y, f"{price:.2f}")
            y -= 16

        # Total
        y -= 8
        c.line(50, y, width - 50, y)
        y -= 18
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "TOTAL")
        c.drawRightString(width - 50, y, f"{total:.2f} €")

        c.showPage()
        c.save()
        buffer.seek(0)

        filename = "facture_prix.pdf"
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf",
        )
    finally:
        db.close()

if __name__ == "__main__":
    # pour docker
    ensure_default_avatar_file()
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
