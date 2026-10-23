"""Fill the database with sample data, so the API has something to show.

Usage: python seed.py
"""

from datetime import date, timedelta

from app.database import DB_PATH, connect, init_db

BOOKS = [
    ("Clean Code", "Robert C. Martin", 2008, "9780132350884", 3),
    ("The Pragmatic Programmer", "Andrew Hunt, David Thomas", 1999, "9780201616224", 2),
    ("Python Crash Course", "Eric Matthes", 2019, "9781593279288", 4),
    ("Database System Concepts", "Abraham Silberschatz", 2019, "9780078022159", 2),
    ("Lalka", "Bolesław Prus", 1890, None, 1),
    ("Solaris", "Stanisław Lem", 1961, None, 2),
]

MEMBERS = [
    ("Anna Kowalska", "anna.kowalska@example.com"),
    ("Piotr Nowak", "piotr.nowak@example.com"),
    ("Katarzyna Wiśniewska", "k.wisniewska@example.com"),
]


def main() -> None:
    init_db()
    with connect() as db:
        db.executescript("DELETE FROM loans; DELETE FROM members; DELETE FROM books;")
        db.executemany(
            "INSERT INTO books (title, author, year, isbn, total_copies) VALUES (?, ?, ?, ?, ?)", BOOKS
        )
        db.executemany("INSERT INTO members (name, email) VALUES (?, ?)", MEMBERS)

        today = date.today()
        book_ids = [r[0] for r in db.execute("SELECT id FROM books ORDER BY id")]
        member_ids = [r[0] for r in db.execute("SELECT id FROM members ORDER BY id")]
        loans = [
            # (book, member, borrowed days ago, returned?)
            (book_ids[0], member_ids[0], 3, False),
            (book_ids[2], member_ids[0], 20, False),  # overdue
            (book_ids[4], member_ids[1], 30, True),
            (book_ids[5], member_ids[2], 1, False),
        ]
        for book_id, member_id, days_ago, returned in loans:
            borrowed = today - timedelta(days=days_ago)
            db.execute(
                "INSERT INTO loans (book_id, member_id, borrowed_at, due_at, returned_at) VALUES (?, ?, ?, ?, ?)",
                (
                    book_id,
                    member_id,
                    borrowed.isoformat(),
                    (borrowed + timedelta(days=14)).isoformat(),
                    (borrowed + timedelta(days=10)).isoformat() if returned else None,
                ),
            )
    print(f"Sample data saved to {DB_PATH}")


if __name__ == "__main__":
    main()
