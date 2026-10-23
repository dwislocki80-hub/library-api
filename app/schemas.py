"""Pydantic models: they validate incoming JSON and describe responses."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)
    year: Optional[int] = Field(default=None, ge=0, le=2100)
    isbn: Optional[str] = Field(default=None, max_length=20)
    total_copies: int = Field(default=1, ge=0)


class Book(BookIn):
    id: int
    available_copies: int


class MemberIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class Member(MemberIn):
    id: int
    joined_at: str


class LoanIn(BaseModel):
    book_id: int
    member_id: int


class Loan(BaseModel):
    id: int
    book_id: int
    member_id: int
    book_title: str
    member_name: str
    borrowed_at: str
    due_at: str
    returned_at: Optional[str]
    overdue: bool
