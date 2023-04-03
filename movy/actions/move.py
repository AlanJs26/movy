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
            if not path.isdir(content):
                if self._eval_argument('makedirs', item) == 'true' and not self.simulate:
                    os.makedirs(content)
                else:
                    raise ActionException(self.name, f'directory {content} does not exist. Use the argument "makedirs" to automatically create missing directories')

            if path.isfile(item.filepath):
                if self._eval_argument('silent', item) != 'true':
                    rprint(f'[yellow not bold]Move: [green]{path.basename(item.filepath)} [blue]-> {path.split(content)[0]+"/" if path.split(content)[0] else ""}[bold]{path.split(content)[1]}')
                if not self.simulate:
                    try:
                        shutil.move(item.filepath, content)
                        item.deleted = True

                    except shutil.Error:
                        rprint(f'[yellow]"{item.filepath}" already exists in destination folder')
                        choice = Confirm.ask(f'overwrite?', default=False)
                        if choice:
                            shutil.move(item.filepath, path.join(content, path.basename(item.filepath)))
                            item.deleted = True

                            rprint(f'[yellow not bold]Move: [green]{path.basename(item.filepath)} [blue]-> {path.split(content)[0]+"/" if path.split(content)[0] else ""}[bold]{path.split(content)[1]}')
                        else:
                            rprint(f'[yellow]ignoring "{path.basename(item.filepath)}"')
                else:
                    item.deleted = True


            else:
                raise ActionException(self.name, 'this action can only move files')
        elif not self.content:
            raise ActionException(self.name, 'destination path is empty')



