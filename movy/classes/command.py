from typing import Iterable
from .content import Expression, Argument
from abc import abstractmethod
from .pipe import PipeItem, Pipe
from rich import print as rprint
from .exceptions import ActionException
from copy import copy


class Destination_rule:
    valid_operators = ['or', 'and', 'reset']

    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        self.operator = operator or [self.valid_operators[0]] # or

        self.name = name

        self.ignore_all_exceptions = ignore_all_exceptions

        self.content = [(item.lstrip() if isinstance(item,str) else item) for item in content]
        self.raw_content = content

        self.arguments = arguments
        self.simulate = False

    def __repr__(self):
        output = f'[green]Action (name: [cyan]{self.name}[green], operator: [cyan]{self.operator}[green])  '
        if self.content:
            output += '['
            for i,item in enumerate(self.content):
                output += repr(item)
                if i+1 < len(self.content):
                    output += ','
            output += ']'

        if self.arguments:
            output += '=>\n    '

            for child in self.arguments:
                output += repr(child)
        else:
            output += '\n'

        return output

    def _get_argument(self, key:str):
        for argument in self.arguments:
            if argument.name == key:
                return argument.content
        return None

    def _eval_argument(self, key:str, pipe_item: PipeItem):
        arg = self._get_argument(key)
        if arg:
            return Expression.eval_list(arg, pipe_item)
        return None

    def _eval_raw_content(self, pipe_item: PipeItem):
        return Expression.eval_list(self.raw_content, pipe_item)

    def _eval_content(self, pipe_item: PipeItem):
        return Expression.eval_list(self.content, pipe_item)

    def eval(self, pipe: Pipe) -> None:
        for item in copy(pipe.items):
            if item.deleted:
                continue
            try:
                self.eval_item(item, pipe)
            except ActionException as e:
                if not self.ignore_all_exceptions:
                    rprint(str(e))

    @abstractmethod
    def eval_item(self, item: PipeItem, pipe: Pipe) -> None:
        raise NotImplementedError('Eval not implemented')

class Input_rule:
    valid_operators = ['or', 'and', 'reset', 'not']
    required_operators = ['or', 'and', 'reset']

    def __init__(self, name: str, operator:list[str], content: list[str|Expression], arguments: list[Argument], flags: list[str], ignore_all_exceptions=False):
        self.operator = operator or [self.valid_operators[0]]

        if all(item not in self.required_operators for item in self.operator):
            self.operator.insert(0, self.valid_operators[0])

        self.flags: list[str] = flags
        self.name = name

        self.ignore_all_exceptions = ignore_all_exceptions

        self.content = [(item.lstrip() if isinstance(item,str) else item) for item in content]
        self.raw_content = content

        self.arguments: list[Argument] = arguments

    def __repr__(self):
        output = f'[green]Rule (name: [cyan]{self.name}[green], operator: [cyan]{self.operator}[green], flags: [cyan]{self.flags}[green])  '

        if self.content:
            output += '['
            for i,item in enumerate(self.content):
                output += repr(item)
                if i+1 < len(self.content):
                    output += ','
            output += ']'

        if self.arguments:
            output += '=>\n'
            for child in self.arguments:
                output += '        '+repr(child)+'\n'
            output += '\n'
        else:
            output += '\n'

        return output

    def _get_argument(self, key:str):
        for argument in self.arguments:
            if argument.name == key:
                return argument.content
        return None

    def _eval_argument(self, key:str, pipe_item: PipeItem):
        arg = self._get_argument(key)
        if arg:
            return Expression.eval_list(arg, pipe_item)
        return None

    def _eval_raw_content(self, pipe_item: PipeItem):
        return Expression.eval_list(self.raw_content, pipe_item)

    def _eval_content(self, pipe_item: PipeItem):
        return Expression.eval_list(self.content, pipe_item)

    @abstractmethod
    def add_callback(self, root:str) -> Iterable[PipeItem]:
        return []
        
    @abstractmethod
    def filter_callback(self, pipe_item: PipeItem) -> bool:
        raise NotImplementedError('filter_callback not implemented')
