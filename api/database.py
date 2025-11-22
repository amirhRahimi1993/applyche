"""
Database connection and utilities for FastAPI
"""
import os
from contextlib import contextmanager
from typing import Generator
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv("model/server_info.env")


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.db_name = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASS")
        self.host = os.getenv("DB_HOST")
        self.port = 5433
        self._connection = None
    
    def connect(self):
        """Create a new database connection"""
        try:
            self._connection = psycopg.connect(
                dbname=self.db_name,
                user=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                sslmode="prefer"
            )
            return self._connection
        except psycopg.OperationalError as e:
            print(f"❌ Connection failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection, None, None]:
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.connect()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self) -> Generator[psycopg.Cursor, None, None]:
        """Context manager for database cursors"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()


# Global database instance
db = Database()


