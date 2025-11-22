from model.professor_list import professor_list

class ProfessorsController:
    def __init__(self,path):
        self.path = path
    def send_professor_info(self):
        professors = professor_list(self.path)
        self.header = professors.return_headers()
        self.nan_columns = professors.return_column_with_nans()
        self.df = professors.returner_file()
        return {"header":self.header, "nans":self.nan_columns , "df":self.df}
