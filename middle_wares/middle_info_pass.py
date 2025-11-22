import pandas as pd

class middle_info_pass:
    def __init__(self):
        self.store_data_variable ={"txt_main_mail":"","txt_first_reminder":"","txt_second_reminder":"","txt_third_reminder":"","professor_list":pd.DataFrame}
    def store_data(self,key,value):
        self.store_data_variable[key] = value
    def get_data(self,key):
        if key in self.store_data_variable.keys():
            return self.store_data_variable[key]
        else:
            return f"For {key} there is not information!"
