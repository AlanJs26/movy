from ..classes import Destination_rule, Pipe, Expression, Argument, Regex
from ..utils import ActionException
from rich import print as rprint
import os
import shutil

class Move(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str]):
        super().__init__(name, content, arguments, operator)

    def eval(self, pipe:Pipe):

        for item in pipe.items:
            content = self._eval_content(item)

            if isinstance(content, Regex):
                raise ActionException(self.name, 'cannot use Regex as argument')

            if content:
                if not os.path.isdir(content):
                    if self._eval_argument('makedirs', item) == 'true':
                        os.makedirs(content)
                    else:
                        raise ActionException(self.name, f'directory {content} does not exist. Use the argument "makedirs" to automatically create missing directories')

                if os.path.isfile(item.filepath):
                    if self._eval_argument('silent', item) != 'true':
                        rprint(f'[yellow]Move: [green]{item.filepath} [cyan]-> [green]{content}')
                    if not self.simulate:
                        shutil.move(item.filepath, content)
                else:
                    raise ActionException(self.name, 'this action can only move files')
            else:
                raise ActionException(self.name, 'destination path is empty')



