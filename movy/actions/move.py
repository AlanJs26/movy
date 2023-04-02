from ..classes import Destination_rule, Pipe, Expression, Argument, Regex, PipeItem
from ..classes.exceptions import ActionException
from rich import print as rprint
from rich.prompt import Confirm
import os
import shutil
from os import path

class Move(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        super().__init__(name, content, arguments, operator, ignore_all_exceptions)

    def eval_item(self, item: PipeItem, pipe: Pipe):
        content = self._eval_content(item)

        if isinstance(content, Regex):
            raise ActionException(self.name, 'cannot use Regex as argument')

        if content:
            if not os.path.isdir(content) and not self.simulate:
                if self._eval_argument('makedirs', item) == 'true':
                    os.makedirs(content)
                else:
                    raise ActionException(self.name, f'directory {content} does not exist. Use the argument "makedirs" to automatically create missing directories')

            if os.path.isfile(item.filepath):
                if self._eval_argument('silent', item) != 'true':
                    rprint(f'[yellow]Move: [green]{item.filepath} [cyan]-> [green]{content}')
                if not self.simulate:
                    try:
                        shutil.move(item.filepath, content)
                    except shutil.Error:
                        rprint(f'[yellow]"{item.filepath}" already exists in destination folder')
                        choice = Confirm.ask(f'overwrite?')
                        if choice:
                            shutil.move(item.filepath, path.join(content, path.basename(item.filepath)))
                            rprint(f'[yellow]Move: [green]{item.filepath} [cyan]-> [green]{content}')
                        else:
                            rprint(f'[green]ignoring "{item.filepath}"')


            else:
                raise ActionException(self.name, 'this action can only move files')
        elif not self.content:
            raise ActionException(self.name, 'destination path is empty')



