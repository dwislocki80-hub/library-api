"""Endpoints for borrowing and returning books.

Business rules:
- a book can be borrowed only if at least one copy is available,
- a member can have at most MAX_ACTIVE_LOANS books at the same time,
- a loan lasts LOAN_DAYS days; after that it is reported as overdue.
"""

import sqlite3
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db
from ..schemas import Loan, LoanIn

router = APIRouter(prefix="/loans", tags=["loans"])

LOAN_DAYS = 14
MAX_ACTIVE_LOANS = 3

LOAN_SELECT = """
    SELECT l.*,
           b.title AS book_title,
           m.name  AS member_name,
           (l.returned_at IS NULL AND l.due_at < date('now')) AS overdue
    FROM loans l
    JOIN books   b ON b.id = l.book_id
    JOIN members m ON m.id = l.member_id
"""


def fetch_loan(db: sqlite3.Connection, loan_id: int) -> dict:
    row = db.execute(LOAN_SELECT + " WHERE l.id = ?", (loan_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Loan {loan_id} not found")
    return dict(row)


@router.get("", response_model=list[Loan])
def list_loans(active: bool = False, db: sqlite3.Connection = Depends(get_db)):
    sql = LOAN_SELECT + (" WHERE l.returned_at IS NULL" if active else "")
    return [dict(r) for r in db.execute(sql + " ORDER BY l.borrowed_at DESC")]


@router.get("/overdue", response_model=list[Loan])
def overdue_loans(db: sqlite3.Connection = Depends(get_db)):
    sql = LOAN_SELECT + " WHERE l.returned_at IS NULL AND l.due_at < date('now') ORDER BY l.due_at"
    return [dict(r) for r in db.execute(sql)]


@router.post("", response_model=Loan, status_code=status.HTTP_201_CREATED)
def borrow_book(loan: LoanIn, db: sqlite3.Connection = Depends(get_db)):
    book = db.execute(
        """SELECT b.total_copies - COUNT(l.id) AS available
           FROM books b
           LEFT JOIN loans l ON l.book_id = b.id AND l.returned_at IS NULL
           WHERE b.id = ? GROUP BY b.id""",
        (loan.book_id,),
    ).fetchone()
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Book {loan.book_id} not found")
    if not db.execute("SELECT 1 FROM members WHERE id = ?", (loan.member_id,)).fetchone():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Member {loan.member_id} not found")
    if book["available"] <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "No copies of this book are available")

    active = db.execute(
        "SELECT COUNT(*) FROM loans WHERE member_id = ? AND returned_at IS NULL",
        (loan.member_id,),
    ).fetchone()[0]
    if active >= MAX_ACTIVE_LOANS:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Member already has {MAX_ACTIVE_LOANS} borrowed books"
        )

    today = date.today()
    cur = db.execute(
        "INSERT INTO loans (book_id, member_id, borrowed_at, due_at) VALUES (?, ?, ?, ?)",
        (loan.book_id, loan.member_id, today.isoformat(), (today + timedelta(days=LOAN_DAYS)).isoformat()),
    )
    return fetch_loan(db, cur.lastrowid)


@router.post("/{loan_id}/return", response_model=Loan)
def return_book(loan_id: int, db: sqlite3.Connection = Depends(get_db)):
    loan = fetch_loan(db, loan_id)
    if loan["returned_at"] is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "This book has already been returned")
    db.execute("UPDATE loans SET returned_at = ? WHERE id = ?", (date.today().isoformat(), loan_id))
    return fetch_loan(db, loan_id)
