"""
SentinelSIF – Database Engine and Session Setup
================================================
Configures SQLAlchemy engine for local SQLite (sentinelsif.db).

NOTE: This project previously attempted PostgreSQL first, with a fallback
to SQLite if PostgreSQL was unreachable. That fallback caused a slow
2-second connection-timeout delay and a confusing warning log on every
startup (including during demos). Since SQLite is sufficient for this
project's scale and demo needs, PostgreSQL support has been removed for
simplicity and reliability. If PostgreSQL support is needed again later,
set the DATABASE_URL environment variable and reintroduce the connection
logic below.
"""

import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("sentinelsif.database")
load_dotenv()

# Allow override via .env / environment variable if ever needed again,
# otherwise default straight to local SQLite — no PostgreSQL connection
# attempt, no timeout delay, no fallback warning.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinelsif.db")

logger.info(f"Using database: {DATABASE_URL}")

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()