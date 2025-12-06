import string
import pandas as pd

"""
    This file is exception it doesnot work with db it works with excel or csv
"""
class professor_list:
    def __init__(self,path):
        self.null_values ={}
        if path.endswith('.xlsx'):
            # Read Excel with first row as header, raw format
            self.df = pd.read_excel(path, header=0, engine='openpyxl')
        elif path.endswith('.csv'):
            # Read CSV with first row as header, raw format
            self.df = pd.read_csv(path, header=0)
        elif path.endswith('.xls'):
            # Read old Excel format
            self.df = pd.read_excel(path, header=0, engine='xlrd')
        else:
            raise "File type not supported only .csv or .xlsx file acceptable"
        
        # Validate that first row is header (check if columns exist)
        if len(self.df.columns) == 0:
            raise ValueError("File must have a header row as the first row. Please ensure your CSV/Excel file has column names in the first row.")
        
        # Validate that column names are not all numeric (which would indicate data was read as header)
        # This is a heuristic check - if all column names are purely numeric, it's likely the header wasn't read correctly
        numeric_col_count = 0
        for col in self.df.columns:
            col_str = str(col).strip()
            # Check if column name is purely numeric (allowing for decimal points and negatives)
            if col_str.replace('.', '').replace('-', '').replace('+', '').isdigit() or col_str.isdigit():
                numeric_col_count += 1
        
        # If all columns are numeric and we have data rows, warn that header might be missing
        if numeric_col_count == len(self.df.columns) and len(self.df.columns) > 0 and len(self.df) > 0:
            raise ValueError("First row must be header row with column names. The file appears to have numeric column names, which suggests the header row is missing. Please ensure your CSV/Excel file has text column names in the first row.")
        
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

