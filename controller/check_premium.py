class CheckPremium:
    premium_mail = 100
    freemium_mail = 15
    def __init__(self,email,password):
        self.email = email
        self.password = password
    def check_premium(self):
        '''Check premium status based on data base but now dummy code'''
        return True