PRAGMA foreign_keys = ON;

INSERT INTO users (name, email, role)
VALUES ('An Nguyen', 'an@example.com', 'requester');

INSERT INTO users (name, email, role)
VALUES ('Binh Tran', 'binh@example.com', 'agent');

INSERT INTO tickets (title, body, requester_id)
VALUES ('May khong len mang', 'May phong ke toan mat mang tu sang.', 1);

INSERT INTO tickets (title, body, priority, requester_id)
VALUES ('Cap quyen thu muc', 'Can quyen ghi vao thu muc bao cao.', 'high', 1);

INSERT INTO tickets (title, body, status, requester_id)
VALUES ('Quen mat khau mail', 'Khong dang nhap duoc mail cong ty.', 'doing', 1);

SELECT id, title, status FROM tickets;

SELECT tickets.id, tickets.title, users.name
FROM tickets
JOIN users ON users.id = tickets.requester_id;

SELECT id, title, status
FROM tickets
WHERE status = 'open';