from ..classes import Destination_rule, Pipe, Expression, Argument, PipeItem
from ..classes.exceptions import ActionException
from rich import print as rprint
import os
from rich.prompt import Confirm

class Trash(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        super().__init__(name, content, arguments, operator, ignore_all_exceptions)

    def eval_item(self, item: PipeItem, pipe: Pipe):
        content = self._eval_content(item)

        if content:
            raise ActionException(self.name, 'this action does not accept content')

        if os.path.isfile(item.filepath):
            if self._eval_argument('confirm', item) != 'false':
                choice = Confirm.ask(f'[red]delete "{item.filepath}"?')
                if not choice:
                    return
            if self._eval_argument('silent', item) != 'true':
                rprint(f'[red]Trash: [green]{item.filepath}')

            if not self.simulate:
                os.system(f'trash "{item.filepath}"')

        else:
            raise ActionException(self.name, 'this action can only trash files')



