-- Database schema for the library API (SQLite)

CREATE TABLE IF NOT EXISTS books (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    author        TEXT    NOT NULL,
    year          INTEGER,
    isbn          TEXT    UNIQUE,
    total_copies  INTEGER NOT NULL DEFAULT 1 CHECK (total_copies >= 0)
);

CREATE TABLE IF NOT EXISTS members (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    joined_at  TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS loans (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id      INTEGER NOT NULL REFERENCES books(id)   ON DELETE CASCADE,
    member_id    INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    borrowed_at  TEXT    NOT NULL,
    due_at       TEXT    NOT NULL,
    returned_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_loans_active ON loans (book_id) WHERE returned_at IS NULL;
