"""API tests. Each test gets a fresh, empty database in a temporary folder.

Run: pytest
"""

import pytest
from fastapi.testclient import TestClient

from app.database import connect, get_db, init_db
from app.main import app


@pytest.fixture
def db_file(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def client(db_file):
    def override_db():
        conn = connect(db_file)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def add_book(client, title="Solaris", copies=1):
    return client.post("/books", json={"title": title, "author": "Stanisław Lem", "total_copies": copies}).json()


def add_member(client, email="anna@example.com"):
    return client.post("/members", json={"name": "Anna", "email": email}).json()


def test_create_and_get_book(client):
    book = add_book(client, copies=2)
    assert book["available_copies"] == 2
    assert client.get(f"/books/{book['id']}").json()["title"] == "Solaris"


def test_missing_book_returns_404(client):
    assert client.get("/books/999").status_code == 404


def test_invalid_data_is_rejected(client):
    assert client.post("/books", json={"title": "", "author": "X"}).status_code == 422
    assert client.post("/members", json={"name": "A", "email": "not-an-email"}).status_code == 422


def test_search_books(client):
    add_book(client, "Solaris")
    add_book(client, "Clean Code")
    results = client.get("/books", params={"q": "clean"}).json()
    assert [b["title"] for b in results] == ["Clean Code"]


def test_borrow_reduces_available_copies(client):
    book, member = add_book(client, copies=2), add_member(client)
    r = client.post("/loans", json={"book_id": book["id"], "member_id": member["id"]})
    assert r.status_code == 201
    assert r.json()["overdue"] is False
    assert client.get(f"/books/{book['id']}").json()["available_copies"] == 1


def test_cannot_borrow_unavailable_book(client):
    book = add_book(client, copies=1)
    m1, m2 = add_member(client, "a@example.com"), add_member(client, "b@example.com")
    client.post("/loans", json={"book_id": book["id"], "member_id": m1["id"]})
    r = client.post("/loans", json={"book_id": book["id"], "member_id": m2["id"]})
    assert r.status_code == 409


def test_member_loan_limit(client):
    member = add_member(client)
    for i in range(3):
        b = add_book(client, f"Book {i}")
        assert client.post("/loans", json={"book_id": b["id"], "member_id": member["id"]}).status_code == 201
    extra = add_book(client, "Book 4")
    r = client.post("/loans", json={"book_id": extra["id"], "member_id": member["id"]})
    assert r.status_code == 409


def test_return_book(client):
    book, member = add_book(client), add_member(client)
    loan = client.post("/loans", json={"book_id": book["id"], "member_id": member["id"]}).json()
    r = client.post(f"/loans/{loan['id']}/return")
    assert r.status_code == 200 and r.json()["returned_at"] is not None
    assert client.get(f"/books/{book['id']}").json()["available_copies"] == 1
    assert client.post(f"/loans/{loan['id']}/return").status_code == 409


def test_cannot_delete_book_on_loan(client):
    book, member = add_book(client), add_member(client)
    client.post("/loans", json={"book_id": book["id"], "member_id": member["id"]})
    assert client.delete(f"/books/{book['id']}").status_code == 409


def test_overdue_loans(client, db_file):
    book, member = add_book(client), add_member(client)
    loan = client.post("/loans", json={"book_id": book["id"], "member_id": member["id"]}).json()
    # move the due date into the past directly in the database
    with connect(db_file) as db:
        db.execute("UPDATE loans SET due_at = '2000-01-01' WHERE id = ?", (loan["id"],))
    overdue = client.get("/loans/overdue").json()
    assert len(overdue) == 1 and overdue[0]["overdue"] is True
