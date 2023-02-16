from ..classes import Destination_rule, Pipe, Expression, Argument, Regex
from rich import print as rprint

class Echo(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: str):
        super().__init__(name, content, arguments, operator)

    def eval(self, pipe:Pipe):

        for item in pipe.items:
            content = Expression.eval_content(self.content, item)

            if isinstance(content, Regex):
                raise Exception('Echo does not support Regex as argument')

            if content:
                rprint(content)
            else:
                rprint(f'[yellow]Echo: [green]"{item.filepath}"')



