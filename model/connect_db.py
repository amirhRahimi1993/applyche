import psycopg
from dotenv import load_dotenv
import os

load_dotenv("server_info.env")

class connect_to_db:
    def __init__(self):
        self.db_name = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASS")
        self.host = os.getenv("DB_HOST")
        self.column_storage = {
            "main_mail" : "is_main_mail_send",
            "first_reminder": "is_first_reminder_send",
            "second_reminder": "is_second_reminder_send",
            "third_reminder": "is_third_reminder_send"
        }
    def return_username_password(self):
        return self.username , self.password
    def connect(self):
        self.conn = None
        try:
            self.conn = psycopg.connect(
                dbname=self.db_name,
                user=self.username,
                password=self.password,
                host=self.host,
                port=5433,           # default Postgres port
                sslmode="prefer"     # change to "require" if server enforces SSL
            )
            print("✅ Connected successfully")
            cur = self.conn.cursor()
            cur.execute("select count(is_main_mail_send) as main_mail  from email_report  where is_main_mail_send = true group by pk;")
        except psycopg.OperationalError as e:
            print("❌ Connection failed:", e)
        return self.conn
