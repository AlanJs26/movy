
class RuleException(Exception):
    def __init__(self, action_name: str, message:str):
        self.action_name = action_name
        self.message = message

    def __str__(self):
        output = f'[red]{self.action_name}: {self.message}'

        return output

class ActionException(Exception):
    def __init__(self, action_name: str, message:str):
        self.action_name = action_name
        self.message = message

    def __str__(self):
        output = f'[red]{self.action_name}: {self.message}'

        return output

class ExpressionException(Exception):
    def __init__(self, content:str, message:str):
        self.content = content
        self.message = message

    def __str__(self):
        output = f'''[red]Expression: {self.content}
        {self.message}'''

        return output



