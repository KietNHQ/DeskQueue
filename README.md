# DeskQueue

Internal help-desk tracker. Staff open a ticket (machine broken, access request, forgotten password). An agent changes the status and must write a note. The list page shows how many tickets are open, in progress, or done.

Built to practice relational data, server-side checks, and a small web flow.

## Stack

- Python, FastAPI, Jinja2
- SQLite (one file: `deskqueue.db`)
- Session cookie for login

No Docker. Runs on your machine.

## Setup

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn jinja2 itsdangerous python-multipart
python app.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install fastapi uvicorn jinja2 itsdangerous python-multipart
python app.py
```

Open http://127.0.0.1:8000

## Demo accounts

| Role | Email | Password |
|------|--------|----------|
| Requester | an@example.com | an123456 |
| Agent | binh@example.com | binh123456 |

Requester sees only their own tickets and can create new ones. Agent sees every ticket, can change status, and must enter a note. The note is stored in the `notes` table.

## Data model

- `users`: id, name, email (unique), role (`requester` or `agent`), password hash and salt
- `tickets`: id, title, body, status (`open` / `doing` / `done`), priority (`low` / `normal` / `high`), `requester_id` (foreign key), created_at
- `notes`: id, `ticket_id`, `author_id`, body, created_at

A ticket belongs to one requester. A note belongs to one ticket and one author. Status changes without a note are rejected on the server.

## What is checked on the server

- Password is hashed with PBKDF2 and a per-user salt. Plain text is never stored.
- `requester_id` comes from the session, not from the form.
- Only an agent can change status. Hiding the button in HTML is not enough; the route checks the role.
- Empty note is rejected before the update.

## Project layout

```
DeskQueue/
  app.py
  schema.sql
  seed.sql
  notes.sql
  requirements.txt
  templates/
    login.html
    tickets.html
  deskqueue.db   # not in git
```
## Filter

`/tickets?status=open` shows only open tickets. Same for `doing` and `done`. `/tickets` shows all. A requester still only sees their own tickets.

## Due date

New tickets can set `due_at`. A ticket is overdue when `due_at` is before today and status is not `done`. The list marks it `(qua han)`.

## What I practiced

- Schema with primary keys, foreign keys, and CHECK constraints
- INSERT, JOIN, filtered SELECT, and conditional counts
- Login session and role-based routes
- Form validation on the server
- Git commits that exclude the virtualenv and the database file.