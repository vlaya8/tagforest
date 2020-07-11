class UserError(Exception):

    def __init__(self, message, context_name):

        self.message = message
        self.context_name = context_name

class FormError(Exception):

    def __init__(self, invalid_form):

        self.invalid_form = invalid_form
