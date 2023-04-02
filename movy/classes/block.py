from .pipe import PipeItem, Pipe
from .command import Input_rule, Destination_rule
from .history import History
import os
from typing import Optional, List
from rich import print as rprint
from ..classes.exceptions import ActionException

class Block:
    def __init__(self, name: str):
        self.root: str
        self.name = name
        self.commands: List[Input_rule|Destination_rule] = []
        self.metadata: dict = {}

        self.ignore_all_exceptions = False

        self.history = History()

    def __str__(self):
        output = ''
        output += f'[blue]Block (root: {self.root}) [[{self.name}]]\n'

        for item in self.commands:
            output += '[white]    '
            output += repr(item)
            # output += '\n'

        return output

    def eval(self, pipe: Optional[Pipe]=None) -> Pipe:
        if not pipe:
            items: list[PipeItem] = []
            # from rich import print as rprint

            for item in os.listdir(self.root):
                if os.path.isfile(os.path.join(self.root, item)):
                    items.append(PipeItem(os.path.join(self.root, item), []))

            pipe = Pipe(items, self.root)

        pipe.ignore_all_exceptions = self.ignore_all_exceptions

        def attach_history_filter(command: Input_rule):
            def new_callback(pipe_item: PipeItem):
                result = command.filter_callback(pipe_item)
                if result:
                    self.history.append(command, pipe_item)
                return result
            return new_callback

        def attach_history_add(command: Input_rule):
            def new_callback(root: str):
                items = command.add_callback(root)
                self.history.append(command, items)
                return items
            return new_callback


        def attach_flags(command: Input_rule):
            def new_filter(pipe_item: PipeItem):
                result = attach_history_filter(command)(pipe_item)
                if 'not' in command.operator:
                    result = not result
                if result:
                    pipe_item.flags.extend(command.flags)
                return result
            return new_filter



        for i,command in enumerate(self.commands):
            if isinstance(command, Input_rule):
                if i>0:
                    for op in command.operator:
                        if op in Pipe.valid_modes:
                            pipe.mode = op
                            break
                pipe.add(attach_history_add(command))
                pipe.filter(attach_flags(command))
            else:
                if 'simulate' in self.metadata and self.metadata['simulate']:
                    command.simulate = True
                try:
                    command.eval(pipe)
                    self.history.append(command, pipe.items)
                    if 'reset' in command.operator:
                        pipe.filter(lambda _:False)
                except ActionException as e:
                    rprint(str(e))

        return pipe
