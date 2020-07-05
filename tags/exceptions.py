class UserError(Exception):

    def __init__(self, message):

        self.message = message

class FormError(Exception):

    def __init__(self, invalid_form):

        self.invalid_form = invalid_form
