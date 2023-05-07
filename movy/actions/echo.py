from ..classes import Destination_rule, Expression, Argument, Regex, PipeItem, Pipe
from rich import print as rprint
from ..classes.exceptions import ActionException

class Echo(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        super().__init__(name, content, arguments, operator, ignore_all_exceptions)

    def eval_item(self, item:PipeItem, pipe: Pipe):
        content = self._eval_raw_content(item)

        if isinstance(content, Regex):
            raise ActionException(self.name, 'cannot use Regex as argument')

        if content:
            item.data['echo'] = content
            rprint(content)
        elif not self.content:
            item.data['echo'] = f'[yellow]Echo: [green]"{item.filepath}"'
            rprint(f'[yellow]Echo: [green]"{item.filepath}"')



