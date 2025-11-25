from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv("server_info.env")


class Database:
    def __init__(self):
        self.db_name = os.getenv("DB_NAME", "applyche_global")
        self.username = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASS", "applyche")
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5434")

        self.url = f"postgresql+psycopg://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        self.engine = create_engine(self.url, echo=True)

        self.SessionLocal = sessionmaker(bind=self.engine)

    def connect(self):
        try:
            session = self.SessionLocal()
            print("✅ SQLAlchemy connected successfully")



            session.close()

        except Exception as e:
            print("❌ SQLAlchemy Error:", e)


db = Database()
db.connect()
