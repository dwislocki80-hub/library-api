"""Library REST API – application entry point.

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routers import books, loans, members


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables on startup
    yield


app = FastAPI(
    title="Library API",
    description="REST API for a small library: books, members and loans.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(books.router)
app.include_router(members.router)
app.include_router(loans.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "docs": "/docs"}
