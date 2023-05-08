from typing import Iterable, Any
from .content import Expression, Argument, Regex
from abc import abstractmethod
from .pipe import PipeItem, Pipe
from rich import print as rprint
from .exceptions import ActionException, RuleException
from copy import copy


class Destination_rule:
    # all: run action on all items (only on supported actions)
    # reset: reset pipe on next command
    valid_operators = ['all', 'reset']
    default_operator = ''

    def ensure_string(self, content, msg='You should input a string as argument'):
        if not isinstance(content, str):
            raise ActionException(self.name, msg)
        return content

    def ensure_regex(self, content, msg='You should use Regex as argument'):
        if not isinstance(content, Regex):
            raise ActionException(self.name, msg)
        return content

    def ensure_not_empty(self, content, msg='Input field is empty'):
        if not content:
            raise ActionException(self.name, msg)
        return content

    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        self.operator = operator or [self.default_operator] # or

        self.name = name

        self.ignore_all_exceptions = ignore_all_exceptions

        # self.content = [(item.lstrip() if isinstance(item,str) else item) for item in content]
        if len(content):
            self.content = [content[0].lstrip() if isinstance(content[0],str) else content[0], *content[1:]]
        else:
            self.content = content

        self.raw_content = content

        self.arguments = arguments
        self.simulate = False

        self.arguments_defaults:dict[str,Any] = {}

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
        if key in self.arguments_defaults:
            return self.arguments_defaults[key]
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
    def eval_all(self, pipe: Pipe) -> None:
        raise NotImplementedError('Eval All not implemented')

    @abstractmethod
    def eval_item(self, item: PipeItem, pipe: Pipe) -> None:
        raise NotImplementedError('Eval not implemented')

class Input_rule:
    # not: negates the rule
    required_operators = Pipe.valid_modes
    valid_operators = ['not'] + required_operators

    default_operator = 'or'


    def ensure_string(self, content, msg='You should input a string as argument'):
        if not isinstance(content, str):
            raise RuleException(self.name, msg)
        return content

    def ensure_regex(self, content, msg='You should use Regex as argument'):
        if not isinstance(content, Regex):
            raise RuleException(self.name, msg)
        return content

    def ensure_not_empty(self, content, msg='Input field is empty'):
        if not content:
            raise RuleException(self.name, msg)
        return content

    def __init__(self, name: str, operator:list[str], content: list[str|Expression], arguments: list[Argument], flags: list[str], ignore_all_exceptions=False):
        self.operator = operator or [self.default_operator]

        if all(item not in self.required_operators for item in self.operator):
            self.operator.insert(0, self.default_operator)

        self.flags: list[str] = flags
        self.name = name

        self.ignore_all_exceptions = ignore_all_exceptions

        # self.content = [(item.lstrip() if isinstance(item,str) else item) for item in content]
        if len(content):
            self.content = [content[0].lstrip() if isinstance(content[0],str) else content[0], *content[1:]]
        else:
            self.content = content

        self.raw_content = content

        self.arguments_defaults:dict[str,Any] = {}

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
        if key in self.arguments_defaults:
            return self.arguments_defaults[key]
        for argument in self.arguments:
            if argument.name == key:
                return argument.content
        return None
    
    def _content_to_str(self):
        output = ''
        for item in self.content:
            if isinstance(item, Expression):
                output += ' '+item.content
            else:
                output += ' '+item
        return output

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
