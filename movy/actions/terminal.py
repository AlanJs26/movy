from ..classes import Destination_rule, Pipe, Expression, Argument, PipeItem
import shlex
import subprocess
from rich import print as rprint
import os


class Terminal(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        super().__init__(name, content, arguments, operator, ignore_all_exceptions)

    def eval_item(self, item: PipeItem, pipe: Pipe):

        content = self.ensure_string(self._eval_content(item))

        self.ensure_not_empty(self.content)

        if not content:
            return

        cwd = self.ensure_string(self._eval_argument('cwd', item) or os.getcwd())

        if not self.simulate:
            p = subprocess.Popen(shlex.split(content), cwd=cwd, stdout=True)

            out, err = p.communicate()
        else:
            out = b''
            err = False

        item.data['terminal'] = {
            "out": ''
        }


        if not err:
            item.data['terminal']["out"] = out.decode('utf-8')

        if self._eval_argument('verbose', item) == 'true':
            if not err:
                rprint(f'[yellow]Terminal: [green]{content}')
            else:
                rprint(f'[yellow]Terminal: [red]{content}')

            



