from typing import List, Optional, Tuple,Callable, Union
import os
from datetime import datetime
import re

class Block:
    def __init__(self, input_set, destination_set):
        self.input_set : Rule_set = input_set
        self.destination_set : Destination_set = destination_set
        self.root : None|str = None

class Destination_set:
    def __init__(self, children) -> None:
        self.children : List[Destination_rule] = children or []

class Rule_set:
    def __init__(self, name, children) -> None:
        self.name : str = name
        self.children : List[Input_rule] = children or []
        self.root : None|str = None


class Input_rule:
    def __init__(self, name : Union[str, None], content : Union[str, None], action_type : str, nested : bool):
        self.name = name or None
        self.content = content or ''
        self.action_type = action_type or 'regex'
        self.nested = nested
        self.children : List[Input_rule] = []
        self.root = './'
    
    def eval(self, root:Union[str, None]=None):
        if root is None:
            root = self.root    
        regex_match = re.search(r'^\s*\/(.+)\/([a-zA-Z]+)', self.content)
        pattern_string = ''
        pattern_flags = None

        if regex_match:
            pattern_string = regex_match.group(1)
            pattern_flags = getattr(re, regex_match.group(2).split('')[0].upper())

            for flag_string in regex_match.group(2).split('')[1:]:
                pattern_flags |= getattr(re, flag_string.upper())
        else:
            pattern_string = self.content
            pattern_flags = re.MULTILINE

        compiled_regex = re.compile(pattern_string, flags = pattern_flags)

        results = []

        for r, dirs, files in os.walk(root):
              for file in files:
                  if compiled_regex.match(file):
                     results.append(( r+'/'.join(dirs)+'/'+file, self.name))

        return results


    
    

class Destination_rule:
    def __init__(self, content):
        self.content : List[str|Tuple[str,str|None]] = content or []

class HistoryItem:
    def __init__(self, date:Union[str, datetime], input_path : str, destination_path : str):
        self.date : datetime
        if isinstance(date, str):
            # 2022-08-13 13:45
            self.date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
        else:
            self.date = date

        self.input_path = input_path
        self.destination_path = destination_path

class FileHistory:
    def __init__(self, content_string):
        self.history_array : List[HistoryItem] = self.parse(content_string) 

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

    def append(self, date, input_path, destination_path):
        self.history_array.append(HistoryItem(date,input_path,destination_path))
