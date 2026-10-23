"""Endpoints for library members."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db
from ..schemas import Loan, Member, MemberIn
from .loans import LOAN_SELECT

router = APIRouter(prefix="/members", tags=["members"])


def fetch_member(db: sqlite3.Connection, member_id: int) -> dict:
    row = db.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Member {member_id} not found")
    return dict(row)


@router.get("", response_model=list[Member])
def list_members(db: sqlite3.Connection = Depends(get_db)):
    return [dict(r) for r in db.execute("SELECT * FROM members ORDER BY name")]


@router.post("", response_model=Member, status_code=status.HTTP_201_CREATED)
def create_member(member: MemberIn, db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.execute(
            "INSERT INTO members (name, email) VALUES (?, ?)", (member.name, member.email)
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "A member with this email already exists")
    return fetch_member(db, cur.lastrowid)


@router.get("/{member_id}", response_model=Member)
def get_member(member_id: int, db: sqlite3.Connection = Depends(get_db)):
    return fetch_member(db, member_id)


@router.get("/{member_id}/loans", response_model=list[Loan])
def member_loans(member_id: int, db: sqlite3.Connection = Depends(get_db)):
    fetch_member(db, member_id)
    rows = db.execute(LOAN_SELECT + " WHERE l.member_id = ? ORDER BY l.borrowed_at DESC", (member_id,))
    return [dict(r) for r in rows]
