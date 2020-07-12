class LoginRequired(Exception):
    pass

class UserError(Exception):

    def __init__(self, message="", context_name="error_message"):

        self.message = message
        self.context_name = context_name

class UserPermissionError(Exception):

    def __init__(self, message=""):

        self.message = message

class FormError(Exception):

    def __init__(self, invalid_form):

        self.invalid_form = invalid_form
