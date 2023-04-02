from collections.abc import Iterable
from typing import List, overload
from io import StringIO
from .command import Input_rule, Destination_rule
from .content import Expression
from .pipe import PipeItem
from copy import deepcopy

from rich.console import Console
class HistoryItem:
    def __init__(self, command: 'Input_rule|Destination_rule'):

        def expr2str(expressions: list[str|Expression]):
            return ' '.join(a.content if isinstance(a, Expression) else a for a in expressions)

        self.command = command

        self.command_name = command.name
        self.operator = command.operator
        self.content = expr2str(command.content)
        self.arguments = ' '.join(expr2str(a.content) for a in command.arguments)

        if isinstance(command, Input_rule):
            self.flags = command.flags
        else:
            self.flags = []

        self.pipe:list[PipeItem] = [] 

    @overload
    def append(self, item: Iterable[PipeItem]):
        pass

    @overload
    def append(self, item: PipeItem):
        pass

    def append(self, item: PipeItem|Iterable[PipeItem]):
        if isinstance(item, PipeItem):
            self.pipe.append(item)
        else:
            self.pipe.extend(item)

    def __repr__(self):
        console = Console()
        output = StringIO()

        output.write(f'[blue not italic]Item =>')
        output.write(f' [yellow not italic]command_name:[white italic] {self.command_name}')
        output.write(f' [yellow not italic]operator:[white italic] {console.render_str(str(self.operator)).markup}')
        output.write(f' [yellow not italic]content:[white italic] {self.content}')
        output.write(f' [yellow not italic]arguments:[white italic] {self.arguments or "[repr.none]None"}')

        if self.pipe:
            output.write('\n')
        for pipe_item in self.pipe:
            output.write('        ')
            output.write(repr(pipe_item))
            output.write('\n')
        return output.getvalue()


class History:
    def __init__(self):
        self.history_array : List[HistoryItem] = []

    @overload
    def append(self,command: 'Input_rule|Destination_rule', item: Iterable[PipeItem]):
        pass

    @overload
    def append(self,command: 'Input_rule|Destination_rule', item: PipeItem):
        pass

    def append(self,command: 'Input_rule|Destination_rule', item: PipeItem|Iterable[PipeItem]):
        history_item = None
        for h_item in self.history_array:
            if h_item.command == command:
                history_item = h_item
                break

        if not history_item:
            history_item = HistoryItem(command)
            self.history_array.append(history_item)

        history_item.append(deepcopy(item))

    def __repr__(self):
        output = StringIO()
        output.write('[blue]History\n')
        for item in self.history_array:
            output.write(f'    {item}\n')
        return output.getvalue()
