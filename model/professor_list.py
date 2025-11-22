import string
import pandas as pd

"""
    This file is exception it doesnot work with db it works with excel or csv
"""
class professor_list:
    def __init__(self,path):
        self.null_values ={}
        if path.endswith('.xlsx'):
            self.df = pd.read_excel(path)
        elif path.endswith('.csv'):
            self.df = pd.read_csv(path)
        else:
            raise "File type not supported only .csv or .xlsx file acceptable"
        self.headers = self.df.head()

    def __has_any_letter(self,text: str) -> bool:
        if str(text).lower() == "" or str(text).lower() == "nan" or str(text).lower() == "null":
            return False
        for ch in str(text).lower():
            if ch in string.ascii_lowercase:
                return True
        return False
    def __upload_local_info_into_sever(self):
        print("Uploading part still not implemented!")
    def __check_nanity(self):
        for h in self.headers:
            for i in range(len(self.df[h])):
                if self.__has_any_letter(self.df[h][i]) == False:
                    if h not in self.null_values.keys():
                        self.null_values[h] = []
                    self.null_values[h].append(i)
        return self.null_values

    def returner_file(self):
        return self.df

    def return_column_with_nans(self):

        self.__check_nanity()
        return self.null_values
    def return_headers(self):

        return self.headers.columns.tolist()


if __name__ == '__main__':
    professor = professor_list(r"C:\Users\Acer\OneDrive\Documents\professors.xlsx")
    professor.return_column_with_nans()

