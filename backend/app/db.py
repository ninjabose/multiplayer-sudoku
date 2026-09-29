from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    pass


def init_db(url=None) -> None:
    global engine, SessionLocal
    url = url or os.getenv("DATABASE_URL", "sqlite:///./sudoku.db")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


def session():
    if SessionLocal is None:
        init_db()
    return SessionLocal()
