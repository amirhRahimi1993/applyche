from connect_db import connect_to_db

class EmailTemplateModel:
    def __init__(self):
        self.connection = connect_to_db()
        self.cursor = self.connection.connect()
    def upload_text(self,text):
        pass
    def fetch_text(self):
        pass
