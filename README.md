# Library API

A REST API for a small library, built with **Python**, **FastAPI** and **SQLite**.
It manages books, library members and loans, and enforces real business rules
such as copy availability and a borrowing limit per member.

All database access is written in **plain SQL** (no ORM), so the queries are easy to read
and show how the data is actually joined and aggregated.

## Features

- CRUD for books, with search by title or author and an "available now" filter
- Library members with unique e-mail validation
- Borrowing and returning books
- Business rules:
  - a book can be borrowed only if a copy is available
  - a member can have at most **3** books at the same time
  - a loan lasts **14 days**, after that it is reported as overdue
  - a book that is on loan cannot be deleted
- Automatic, interactive API documentation (Swagger UI) at `/docs`
- 10 automated tests with `pytest`, each running on its own temporary database

## Tech stack

| Area       | Technology                           |
|------------|--------------------------------------|
| Language   | Python 3.10+                         |
| Framework  | FastAPI, Pydantic (validation)       |
| Database   | SQLite, raw SQL (`sqlite3`)          |
| Testing    | pytest, FastAPI TestClient           |

## Project structure

```
library-api/
├── app/
│   ├── main.py          # FastAPI app, registers the routers
│   ├── database.py      # SQLite connection and schema setup
│   ├── schema.sql       # tables: books, members, loans
│   ├── schemas.py       # Pydantic models (request/response validation)
│   └── routers/
│       ├── books.py     # /books endpoints
│       ├── members.py   # /members endpoints
│       └── loans.py     # /loans endpoints and business rules
├── tests/test_api.py    # automated tests
├── seed.py              # fills the database with sample data
└── requirements.txt
```

## Database schema

```
books (id, title, author, year, isbn, total_copies)
members (id, name, email, joined_at)
loans (id, book_id → books, member_id → members, borrowed_at, due_at, returned_at)
```

The number of available copies is not stored. It is calculated on the fly:
`total_copies - number of loans where returned_at IS NULL`.
This way the data can never get out of sync.

## Getting started

```bash
git clone https://github.com/dwislocki80-hub/library-api.git
cd library-api
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python seed.py                 # optional: sample books, members and loans
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** to try every endpoint in the browser.

## Example requests

```bash
# search for available books
curl "http://127.0.0.1:8000/books?q=python&available=true"

# borrow a book
curl -X POST http://127.0.0.1:8000/loans \
     -H "Content-Type: application/json" \
     -d '{"book_id": 1, "member_id": 2}'

# return it
curl -X POST http://127.0.0.1:8000/loans/1/return

# list overdue loans
curl http://127.0.0.1:8000/loans/overdue
```

## Endpoints

| Method | Path                      | Description                          |
|--------|---------------------------|--------------------------------------|
| GET    | `/books`                  | List books (`?q=`, `?available=`)    |
| POST   | `/books`                  | Add a book                           |
| GET    | `/books/{id}`             | Get one book                         |
| PUT    | `/books/{id}`             | Update a book                        |
| DELETE | `/books/{id}`             | Delete a book (not if on loan)       |
| GET    | `/members`                | List members                         |
| POST   | `/members`                | Add a member                         |
| GET    | `/members/{id}/loans`     | Loan history of a member             |
| GET    | `/loans`                  | List loans (`?active=true`)          |
| POST   | `/loans`                  | Borrow a book                        |
| POST   | `/loans/{id}/return`      | Return a book                        |
| GET    | `/loans/overdue`          | Loans past their due date            |

## Running tests

```bash
pytest
```

## Possible next steps

- Authentication (JWT) for librarians
- Reservations queue for unavailable books
- Docker image and PostgreSQL instead of SQLite

## License

MIT
