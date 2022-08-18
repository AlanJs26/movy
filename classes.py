from typing import List, Optional, Tuple,Callable, Union
import os
from datetime import datetime
import re

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

    def extend(self, history : List[HistoryItem]):
        self.history_array.extend(history)

    def toString(self):
        output = ''

        for item in self.history_array:
            output += item.toString() + '\n'

        return output[:-1] 



class Block:
    def __init__(self, input_set, destination_set):
        self.input_set : Rule_set = input_set
        self.destination_set : Destination_set = destination_set
        self.root : None|str = None

    def eval(self, history : Optional[FileHistory] = None):
        input_results = self.input_set.eval_children()
        destination_results = self.destination_set.eval_children(input_results)
        new_history = FileHistory()
        
        new_destination_results = []
        if history:
            for destination in destination_results:
                if not history.has_item(HistoryItem(datetime.now(), destination[0], destination[1])):
                    new_destination_results.append(destination)
                    new_history.append(datetime.now(), destination[0], destination[1])

        return new_history


class Destination_set:
    def __init__(self, children) -> None:
        self.children : List[Destination_rule] = children or []

    def eval_children(self, input_rule_results: List[Tuple[str,Union[None,str]]]):
        results = []

        for item in input_rule_results:
            output = ""
            for child in self.children:
                if output:
                    break
                modified = True
                for value in child.content:
                    if isinstance(value, tuple):
                        modified = False
                        break


                inner_output = ""
                for value in child.content:
                    if isinstance(value, str):
                        inner_output += value
                    elif value[1] is None or value[1] == item[1]:
                        if value[0] == 'basename':
                            inner_output += item[0].split('/')[-1]
                            modified = True
                if modified:
                    output = inner_output
            if output:
                results.append((item[0], output))
        return results

class Rule_set:
    def __init__(self, name, children) -> None:
        self.name : str = name
        self.children : List[Input_rule] = children or []
        self.root : None|str = None

    def eval_children(self):
        results = set()
        previous_operation = 'or'

        for child in self.children:
            current_result = child.eval()
            # print(current_result)

            if previous_operation == 'or':
                results = results.union(current_result)
            elif previous_operation == 'and':
                results = results.intersection(current_result)

            previous_operation = child.operation

        return list(results)

class Input_rule:
    def __init__(self, name : Union[str, None], content : Union[str, None], action_type : Union[str, None], nested : bool):
        self.name = name or None
        self.content = content or ''
        self.action_type = action_type or 'regex'
        self.nested = nested
        self.operation = 'or'
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
            pattern_flags = getattr(re, regex_match.group(2)[0].upper())

            for flag_string in regex_match.group(2)[1:]:
                pattern_flags |= getattr(re, flag_string.upper())
        else:
            pattern_string = self.content
            pattern_flags = re.MULTILINE

        compiled_regex = re.compile(pattern_string, flags = pattern_flags)

        results = []

        for r, dirs, files in os.walk(root):
              for file in files:
                  if compiled_regex.search(r+'/'.join(dirs)+'/'+file):
                     results.append(( r+'/'.join(dirs)+'/'+file, self.name))

        return results


    
    

class Destination_rule:
    def __init__(self, content):
        self.content : List[str|Tuple[str,str|None]] = content or []

