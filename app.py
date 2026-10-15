import hashlib
import secrets
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

BASE = Path(__file__).resolve().parent
DB = BASE / "deskqueue.db"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="deskqueue-local-only", max_age=60 * 60 * 8)
templates = Jinja2Templates(directory=BASE / "templates")


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return digest.hex()


def current_user(request: Request, conn):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


@app.get("/")
def home(request: Request):
    with connect() as conn:
        user = current_user(request, conn)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/tickets", status_code=303)


@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": ""})


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    with connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not user["password_salt"]:
        return templates.TemplateResponse(request, "login.html", {"error": "Sai email hoac mat khau"}, status_code=400)
    if hash_password(password, user["password_salt"]) != user["password_hash"]:
        return templates.TemplateResponse(request, "login.html", {"error": "Sai email hoac mat khau"}, status_code=400)
    request.session["user_id"] = user["id"]
    return RedirectResponse("/tickets", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/tickets")
def tickets(request: Request):
    with connect() as conn:
        user = current_user(request, conn)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if user["role"] == "agent":
            rows = conn.execute(
                """
                SELECT tickets.id, tickets.title, tickets.status, tickets.priority, users.name AS requester
                FROM tickets JOIN users ON users.id = tickets.requester_id
                ORDER BY tickets.id DESC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT tickets.id, tickets.title, tickets.status, tickets.priority, users.name AS requester
                FROM tickets JOIN users ON users.id = tickets.requester_id
                WHERE tickets.requester_id = ?
                ORDER BY tickets.id DESC
                """,
                (user["id"],),
            ).fetchall()
        counts = conn.execute(
            """
            SELECT
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_count,
            SUM(CASE WHEN status = 'doing' THEN 1 ELSE 0 END) AS doing_count,
            SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done_count
            FROM tickets
            """
        ).fetchone()
    return templates.TemplateResponse(request, "tickets.html", {"user": user, "tickets": rows, "counts": counts})


@app.post("/tickets")
def create_ticket(request: Request, title: str = Form(...), body: str = Form(...), priority: str = Form("normal")):
    if priority not in {"low", "normal", "high"}:
        priority = "normal"
    with connect() as conn:
        user = current_user(request, conn)
        if not user:
            return RedirectResponse("/login", status_code=303)
        conn.execute(
            "INSERT INTO tickets (title, body, priority, requester_id) VALUES (?, ?, ?, ?)",
            (title.strip(), body.strip(), priority, user["id"]),
        )
        conn.commit()
    return RedirectResponse("/tickets", status_code=303)


@app.post("/tickets/{ticket_id}/status")
def change_status(
    request: Request,
    ticket_id: int,
    status: str = Form(...),
    note: str = Form(""),
):
    if status not in {"open", "doing", "done"}:
        return RedirectResponse("/tickets", status_code=303)
    note = note.strip()
    if not note:
        return RedirectResponse("/tickets", status_code=303)
    with connect() as conn:
        user = current_user(request, conn)
        if not user or user["role"] != "agent":
            return RedirectResponse("/tickets", status_code=303)
        conn.execute(
            "UPDATE tickets SET status = ? WHERE id = ?",
            (status, ticket_id),
        )
        conn.execute(
            "INSERT INTO notes (ticket_id, author_id, body) VALUES (?, ?, ?)",
            (ticket_id, user["id"], note),
        )
        conn.commit()
    return RedirectResponse("/tickets", status_code=303)


def set_password(conn, email: str, password: str):
    salt = secrets.token_hex(8)
    conn.execute(
        "UPDATE users SET password_salt = ?, password_hash = ? WHERE email = ?",
        (salt, hash_password(password, salt), email),
    )


if __name__ == "__main__":
    with connect() as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if "password_hash" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            conn.execute("ALTER TABLE users ADD COLUMN password_salt TEXT")
        set_password(conn, "an@example.com", "an123456")
        set_password(conn, "binh@example.com", "binh123456")
        conn.commit()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)