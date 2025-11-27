import psycopg
import os
from connect_db import connect_to_db
class Email_Format:
    def __init__(self,email):
        connection = connect_to_db()
        self.conn = connection.connect()
        self.column_keys = 'max_email_per_day,main_email_per_day,reminder1_per_day,reminder2_per_day,reminder3_per_day,delay_time,delay_between_reminders,is_shuffle,is_local_time,email_per_university'
        self.table_name = 'email_format'
        self.email = email
    def load_format(self):
        cur = self.conn.cursor()
        values = cur.execute('SELECT ' + self.column_keys + 'from '+self.table_name + 'where email= ' + self.email + ';')
        return values

    def insert_format(self, information):
        keys = self.column_keys.split(",")  # e.g. "name,age,email"
        cur = self.conn.cursor()

        # Build query parts
        columns = ", ".join(keys)
        placeholders = ", ".join(["%s"] * len(keys))

        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

        # Ensure values are taken in the same order as keys
        values = tuple(information[k] for k in keys)

        cur.execute(query, values)
        self.conn.commit()

        return cur.rowcount  # or cur.lastrowid if you need inserted id


Email_Format()