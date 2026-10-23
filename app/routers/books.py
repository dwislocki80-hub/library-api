"""Endpoints for books: list/search, create, read, update, delete."""

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_db
from ..schemas import Book, BookIn

router = APIRouter(prefix="/books", tags=["books"])

# available_copies = all copies minus copies currently on loan
BOOK_SELECT = """
    SELECT b.*,
           b.total_copies - COUNT(l.id) AS available_copies
    FROM books b
    LEFT JOIN loans l ON l.book_id = b.id AND l.returned_at IS NULL
"""


def fetch_book(db: sqlite3.Connection, book_id: int) -> dict:
    row = db.execute(BOOK_SELECT + " WHERE b.id = ? GROUP BY b.id", (book_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Book {book_id} not found")
    return dict(row)


@router.get("", response_model=list[Book])
def list_books(
    q: Optional[str] = Query(None, description="Search in title or author"),
    available: Optional[bool] = Query(None, description="Only books that can be borrowed now"),
    db: sqlite3.Connection = Depends(get_db),
):
    sql, params = BOOK_SELECT, []
    if q:
        sql += " WHERE b.title LIKE ? OR b.author LIKE ?"
        params += [f"%{q}%", f"%{q}%"]
    sql += " GROUP BY b.id"
    if available:
        sql += " HAVING available_copies > 0"
    sql += " ORDER BY b.title"
    return [dict(r) for r in db.execute(sql, params)]


@router.post("", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book: BookIn, db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.execute(
            "INSERT INTO books (title, author, year, isbn, total_copies) VALUES (?, ?, ?, ?, ?)",
            (book.title, book.author, book.year, book.isbn, book.total_copies),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "A book with this ISBN already exists")
    return fetch_book(db, cur.lastrowid)


@router.get("/{book_id}", response_model=Book)
def get_book(book_id: int, db: sqlite3.Connection = Depends(get_db)):
    return fetch_book(db, book_id)


@router.put("/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookIn, db: sqlite3.Connection = Depends(get_db)):
    current = fetch_book(db, book_id)
    on_loan = current["total_copies"] - current["available_copies"]
    if book.total_copies < on_loan:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{on_loan} copies are on loan, total_copies cannot be lower",
        )
    db.execute(
        "UPDATE books SET title = ?, author = ?, year = ?, isbn = ?, total_copies = ? WHERE id = ?",
        (book.title, book.author, book.year, book.isbn, book.total_copies, book_id),
    )
    return fetch_book(db, book_id)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: sqlite3.Connection = Depends(get_db)):
    book = fetch_book(db, book_id)
    if book["available_copies"] < book["total_copies"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot delete a book that is on loan")
    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
