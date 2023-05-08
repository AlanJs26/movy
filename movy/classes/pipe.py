from rich import print as rprint
from typing import Callable, Iterable

from ..classes.exceptions import ExpressionException, RuleException
from copy import copy
from rich.console import Console
from io import StringIO


class PipeItem():
    def __init__(self, filepath: str, flags: list[str]):
        self.filepath = filepath
        self.flags = flags

        self.deleted = False

        self.data:dict = {
            'path': filepath,
            'flags': flags
        }

    def __repr__(self):
        console = Console()
        output = StringIO()

        output.write('[blue]PipeItem(')

        output.write(f'[yellow]filepath:[white] {self.filepath},')
        output.write(console.render_str(
            f'''[yellow] flags:[white] {self.flags},'''
            f'''[yellow] data:[white] {self.data}'''
        ).markup)
        output.write('[blue])')

        return output.getvalue()

class Pipe():
    valid_modes = ['and', 'or', 'reset', 'pass']

    def __init__(self, items: list[PipeItem], root:str):
        self.original_items = set(items)
        self.items = set(items)
        self.root = root
        self.mode: str = 'and' 

        from .command import Destination_rule, Input_rule

        self.commands: list['Input_rule|Destination_rule'] = []

        self.ignore_all_exceptions = False

    def __repr__(self):
        output = 'Pipe(items: ['
        for item in self.items:
            output += '\n    ' + repr(item) + '\n'

        output+='])'
        return output


    def add(self, callback: Callable[[str], Iterable[PipeItem]]):
        try:
            for item in callback(self.root):
                self.items.add(item)
        except (RuleException, ExpressionException) as e:
            if not self.ignore_all_exceptions:
                rprint(str(e))

    def filter(self, callback: Callable[[PipeItem], bool]):

        match self.mode:
            # do not filter
            case 'pass':
                for item in self.items:
                    try:
                        callback(item)
                    except (RuleException, ExpressionException) as e:
                        if not self.ignore_all_exceptions:
                            rprint(str(e))
            # remove items that do not match (difference)
            case 'and':
                for item in copy(self.items):
                    try:
                        result = callback(item)
                        if result == False:
                            self.items.remove(item)
                    except (RuleException, ExpressionException) as e:
                        self.items.remove(item)
                        if not self.ignore_all_exceptions:
                            rprint(str(e))
            # remove items that match from original items (difference)
            case 'reset':
                self.items = copy(self.original_items)
                for item in copy(self.items):
                    try:
                        result = callback(item)
                        if result == False:
                            self.items.remove(item)
                    except (RuleException, ExpressionException) as e:
                        self.items.remove(item)
                        if not self.ignore_all_exceptions:
                            rprint(str(e))
            # add items that match (union)
            case 'or':
                for item in copy(self.original_items):
                    try:
                        result = callback(item)
                        if result == True:
                            self.items.add(item)
                    except (RuleException, ExpressionException) as e:
                        if not self.ignore_all_exceptions:
                            rprint(str(e))
