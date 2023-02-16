from abc import abstractmethod
from collections.abc import Iterable
from typing import List, Optional, Callable, Union
import os
from datetime import datetime
import re
from copy import copy

class Regex():
    def __init__(self, content:str, flags:list[str]):
        self.content = content
        self.flags = flags
        self.flags_compiled = re.MULTILINE

        for ch in flags:
            flag = getattr(re, ch.upper(), None)

            if flag:
                self.flags_compiled |= flag
            else:
                raise Exception(f'Unknown flag "{ch}" in "/{content}/{"".join(flags)}"')

        self.compiled = re.compile(self.content, flags=self.flags_compiled)

    def search(self, string:str):
        return re.search(self.compiled, string)

    @staticmethod
    def regex():
        return re.compile(r'^\s*\/(?P<content>.+)\/(?P<flags>[a-zA-Z]*)\s*$')

    @staticmethod
    def is_valid(raw_content:str):
        regex_regex=Regex.regex()
        return bool(re.search(regex_regex, raw_content))

    @staticmethod
    def parse(raw_content:str):
        regex_regex=Regex.regex()

        match = re.search(regex_regex, raw_content)
        if not match:
            raise Exception('Invalid Regexp')

        match_dict = match.groupdict()

        return Regex(content=match_dict['content'], flags=[i for i in match_dict['flags']])


class PipeItem():
    def __init__(self, filepath: str, flags: list[str]):
        self.filepath = filepath
        self.flags = flags

        self.data:dict = {
            'path': filepath,
            'flags': flags
        }

class Pipe():
    def __init__(self, items: list[PipeItem], root:str):
        self.original_items = set(items)
        self.items = set(items)
        self.root = root
        self.mode: str = 'and' 

    def add(self, callback: Callable[[str], Iterable[PipeItem]]):
        for item in callback(self.root):
            self.items.add(item)

    def filter(self, callback: Callable[[PipeItem], bool]):
        if self.mode == 'and':
            for item in copy(self.items):
                result = callback(item)
                if result == False:
                    self.items.remove(item)
        elif self.mode == 'reset':
            self.items = copy(self.original_items)
            for item in copy(self.items):
                result = callback(item)
                if result == False:
                    self.items.remove(item)
        elif self.mode == 'or':
            for item in copy(self.original_items):
                result = callback(item)
                if result == True:
                    self.items.add(item)

# TODO -> Add more rules and actions
# TODO -> Implement cli

class Expression():
    def __init__(self, content:str):
        self.content:str = content

    def eval(self, item: PipeItem):
        from os.path import basename

        return eval(self.content, {
            **item.data,
            'basename': basename
        })
    
    @staticmethod
    def eval_content(content: 'list[str|Expression]', pipe_item: PipeItem) -> str|Regex:
        output = ''
        for item in content:
            if isinstance(item, str):
                output += item
                continue

            output += str(item.eval(pipe_item))
        
        if Regex.is_valid(output):
            return Regex.parse(output)

        return output

    def __repr__(self):
        return f'Expression({self.content})'


class Argument():
    def __init__(self, name:str, content:list[str|Expression]):
        self.name = name
        self.content = content

    def __repr__(self):
        return f"Argument(name: '{self.name}', content: {self.content})"


class HistoryItem:
    def __init__(self, date:Union[str, datetime], input_path : str, destination_path : str):
        self.date : datetime
        if isinstance(date, str):
            # 2022-08-13 13:45

            match_date = re.search(r'\[(.+)\]', date)
            if match_date:
                date = match_date.group(1)

            self.date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
        else:
            self.date = date

        self.input_path = input_path
        self.destination_path = destination_path

    def toString(self):
        return f'[{self.date}] {self.input_path} -> {self.destination_path}'

class FileHistory:
    def __init__(self, content_string : Optional[str]=None):
        self.history_array : List[HistoryItem]

        if content_string:
            self.history_array : List[HistoryItem] = self.parse(content_string) 
        else:
            self.history_array = []

    def parse(self, text) -> List[HistoryItem]:
        history = []
        for line in text.splitlines():
            regex_match = re.search(r'(\[.+?])\s*(.+?)\s*->\s*(.+?)(\[|$|\s+)', line)

            if regex_match:
                history_split = regex_match.groups()[:3]
            else:
                continue
            
            history.append(HistoryItem(*history_split)) 


        return history

    def previous_items(self):
        prev_items = []
        last_date = self.history_array[-1].date

        for h_item in reversed(self.history_array):
            if h_item.date > last_date:
                break
            if not os.path.isfile(h_item.destination_path):
                h_item.destination_path = os.path.join(h_item.destination_path, os.path.basename(h_item.input_path))

            if os.path.isfile(h_item.destination_path) and os.path.isfile(h_item.destination_path):
                prev_items.append(h_item)

        return [(item.destination_path, item.input_path, 'move') for item in prev_items]

    def filter(self, callback : Callable[[HistoryItem],bool]):
        self.history_array = [item for item in self.history_array if callback(item)]
    
    def has_item(self, history_item : HistoryItem, until_time : Optional[str] = None) -> bool:
        for item in self.history_array:
            if until_time and datetime.strptime(until_time, '%Y-%m-%d %H:%M:%S.%f') > item.date:
                break
            if history_item.input_path == item.input_path and history_item.destination_path == item.destination_path:
                return True
        return False
            
    def pop(self, n=1):
        for _ in range(n):
            self.history_array.pop()

    def remove(self, input_path, destination_path):
        for item in reversed(self.history_array):
            if item.input_path == input_path and item.destination_path == destination_path:
                self.history_array.remove(item)
                return True

        return False

    def append(self, date, input_path, destination_path):
        self.history_array.append(HistoryItem(date,input_path,destination_path))

    def extend(self, history : List[HistoryItem]):
        self.history_array.extend(history)

    def toString(self):
        output = ''

        for item in self.history_array:
            output += item.toString() + '\n'

        return output[:-1] 

class Block:
    def __init__(self, name: str):
        self.root: str
        self.name = name
        self.commands: List[Input_rule|Destination_rule] = []

    def __str__(self):
        output = ''
        output += f'[blue]Block (root: {self.root}) [[{self.name}]]\n'

        for item in self.commands:
            output += '[white]    '
            output += repr(item)
            # output += '\n'

        return output

    def eval(self, history: FileHistory) -> None:
        items: list[PipeItem] = []
        # from rich import print as rprint

        for item in os.listdir(self.root):
            if os.path.isfile(os.path.join(self.root, item)):
                items.append(PipeItem(os.path.join(self.root, item), []))

        pipe = Pipe(items, self.root)

        def attach_flags(command: Input_rule):
            def new_filter(pipe_item: PipeItem):
                result = command.filter_callback(pipe_item)
                if result:
                    pipe_item.flags.extend(command.flags)
                return result
            return new_filter

        for i,command in enumerate(self.commands):
            if isinstance(command, Input_rule):
                if i>0:
                    pipe.mode = command.operator
                pipe.add(command.add_callback)
                pipe.filter(attach_flags(command))
            else:
                command.eval(pipe)



class Destination_rule:
    valid_operators = ['or', 'and', 'end']

    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: str):
        self.operator = operator or self.valid_operators[0]

        if self.operator not in self.valid_operators:
            raise Exception('Invalid Operator')

        self.name = name
        self.content = content
        self.arguments = arguments

    def __repr__(self):
        output = f'[green]Action (name: [cyan]{self.name}[green], operator: [cyan]{self.operator}[green])  '
        if self.content:
            output += '['
            for i,item in enumerate(self.content):
                output += repr(item)
                if i+1 < len(self.content):
                    output += ','
            output += ']\n'

        if self.arguments:
            output += '=>\n    '

            for child in self.arguments:
                output += repr(child)

        return output

    def eval(self, pipe: Pipe) -> None:
        raise NotImplementedError('Eval not implemented')

class Input_rule:
    valid_operators = ['or', 'and', 'reset']

    def __init__(self, name: str, operator:str, content: list[str|Expression], arguments: list[Argument], flags: list[str]):
        self.operator = operator or self.valid_operators[0]

        if self.operator not in self.valid_operators:
            raise Exception('Invalid Operator')

        self.flags: list[str] = flags
        self.name = name
        self.content:list[str|Expression] = content
        self.arguments: list[Argument] = arguments

    def __repr__(self):
        output = f'[green]Rule (name: [cyan]{self.name}[green], operator: [cyan]{self.operator}[green], flags: [cyan]{self.flags}[green])  '

        if self.content:
            output += '['
            for i,item in enumerate(self.content):
                output += repr(item)
                if i+1 < len(self.content):
                    output += ','
            output += ']\n'

        if self.arguments:
            output += '=>\n    '
        for child in self.arguments:
            output += repr(child)


        return output

    def _get_argument(self, key:str):
        for argument in self.arguments:
            if argument.name == key:
                return argument.content
        return None

    @abstractmethod
    def add_callback(self, root:str) -> Iterable[PipeItem]:
        return []
        
    @abstractmethod
    def filter_callback(self, pipe_item: PipeItem) -> bool:
        raise NotImplementedError('filter_callback not implemented')


