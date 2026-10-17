import sqlite3

conn = sqlite3.connect("deskqueue.db")
cols = {row[1] for row in conn.execute("PRAGMA table_info(tickets)")}
if "due_at" not in cols:
    conn.execute("ALTER TABLE tickets ADD COLUMN due_at TEXT")
    conn.commit()
    print("added due_at")
else:
    print("due_at already exists")
conn.close()