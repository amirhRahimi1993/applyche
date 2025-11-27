"""
Database connection and utilities for FastAPI using SQLAlchemy
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables
load_dotenv("model/server_info.env")

# Database configuration with defaults
# Defaults are for PostgreSQL 18 on localhost:5434
DB_NAME = os.getenv("DB_NAME", "applyche_global")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "applyche")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5434"))  # PostgreSQL 18 default port

# SQLAlchemy connection URL
# Using psycopg (psycopg3) driver
# Format: postgresql+psycopg://user:password@host:port/database
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine with connection pooling for better performance
# QueuePool is the default and provides connection reuse
try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,  # Number of connections to maintain in the pool
        max_overflow=20,  # Maximum number of connections beyond pool_size
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False,  # Set to True for SQL query logging
    )
except Exception as e:
    print(f"Warning: Could not create database engine: {e}")
    print(f"Database URL: postgresql+psycopg://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Please ensure:")
    print(f"  1. PostgreSQL is running on {DB_HOST}:{DB_PORT}")
    print(f"  2. Database '{DB_NAME}' exists (run 'python setup_database.py')")
    print(f"  3. Credentials in model/server_info.env are correct")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    Use this in FastAPI route dependencies
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    Use this for manual session management
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Import models to ensure they're registered
from api.db_models import Base

# Create all tables (optional - usually handled by migrations)
# Base.metadata.create_all(bind=engine)


