from typing import List, Optional, Tuple,Callable, Union
import os
from datetime import datetime
import re
from rich import print

def parse_action(text:str, action_type:str, pattern_string : Optional[str] = None, flags=re.MULTILINE) -> Tuple[str,bool]:
    new_text = ''
    
    if action_type == 'regex':
        new_text = text
    elif action_type == 'basename':
        new_text = re.split(r'[/\\]', text)[-1]

    if pattern_string is not None:
        return '', bool(re.search(pattern_string, new_text, flags = flags)) 

    if new_text:
        return new_text, True

    return text, False


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
            if h_item.date != last_date:
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
    def __init__(self, input_set, destination_set):
        self.input_set : Rule_set = input_set
        self.destination_set : Destination_set = destination_set
        self.root : None|str = None
        self.type = 'rule_set' # rule_set | routine

    def eval(self, history : Optional[FileHistory] = None):
        if self.type == 'routine':
            return []

        input_results = self.input_set.eval_children()
        destination_results = self.destination_set.eval_children(input_results)
        
        new_destination_results = []
        if history:
            for destination in destination_results:
                if not history.has_item(HistoryItem(datetime.now(), destination[0], destination[1])):
                    new_destination_results.append(destination)
                    history.append(datetime.now(), destination[0], destination[1])

        return destination_results

    def run_routine(self, blocks):
        if self.type != 'routine':
            return []

        block_names = [block.input_set.name for block in blocks]

        blocks_pending = []
        for rule in self.input_set.children:
            if rule.content.strip() not in block_names:
                continue
            current_block = blocks[block_names.index(rule.content.strip())]

            now = datetime.now()
            current_time = f'{now.hour}h{now.minute}m'

            if (rule.action_content and current_time == rule.action_content.strip()) or rule.action_content == None: 
                blocks_pending.append(current_block)

        return blocks_pending

class Destination_set:
    def __init__(self, children) -> None:
        self.children : List[Destination_rule] = children or []

    def eval_children(self, input_rule_results: List[Tuple[str,Union[None,str]]]):
        results = []


        for input_match in input_rule_results:
            command_name = 'move'
            output = ""
            for child in self.children:
                command_name = child.command
                found_error = False

                has_tuple = any(map(lambda x : isinstance(x,tuple), child.content))
                if not has_tuple:
                    output = ''.join(child.content)
                    break


                inner_output = ""
                for destination_item in child.content:
                    if found_error:
                        break
                    if isinstance(destination_item, str):
                        inner_output += destination_item
                    elif destination_item[1] is None or destination_item[1] == input_match[1]: # group name
                        parsed_action_text, parse_status = parse_action(input_match[0], destination_item[0])
                        inner_output += parsed_action_text
                        if parse_status == False:
                            found_error = True
                    else:
                        found_error = True

                if not found_error:
                    output = inner_output
                    break

            if output:
                results.append((input_match[0], output, command_name))
        return results

class Input_rule:
    def __init__(self, name : Union[str, None], content : Union[str, None], action_type : Union[str, None], nested : bool):
        self.name = name or None
        self.content = content or ''
        self.action_type = action_type or 'regex'
        self.nested = nested
        self.operation = 'or'
        self.children : List[Input_rule] = []
        self.root = './'
        self.action_content = None

        time_match = re.search(r'(^\d+h$)|(^\d+h\d+m$)', self.action_type.strip())
        if time_match:
            time_split = time_match.string.split('h')
            hour = time_split[0]
            minute = time_split[1].replace('m','')or'0'
            self.action_content = f'{int(hour)}h{int(minute)}m'
            self.action_type = 'time'

    
    def eval(self, root:Union[str, None]=None):
        if root is None:
            root = self.root    
        regex_match = re.search(r'^\s*\/(.+)\/([a-zA-Z]+)', self.content)
        pattern_string = ''
        pattern_flags = None

        if self.action_type == 'time':
            return []

        if regex_match:
            pattern_string = regex_match.group(1)
            pattern_flags = getattr(re, regex_match.group(2)[0].upper())

            for flag_string in regex_match.group(2)[1:]:
                pattern_flags |= getattr(re, flag_string.upper())
        else:
            pattern_string = self.content
            pattern_flags = re.MULTILINE

        results = []

        for file in os.listdir(root):
            _, parse_status = parse_action(root+'/'+file, self.action_type, pattern_string, flags = pattern_flags)
            if parse_status:
                results.append(( root+'/'+file, self.name))

        return results
    
class Rule_set:
    def __init__(self, name : str, children : Union[List[Input_rule],None]) -> None:
        self.name = name
        self.children = children or []
        self.root : None|str = None

    def eval_children(self):
        results = set()
        previous_operation = 'or'

        for child in self.children:
            current_result = child.eval(self.root)

            for output_item in list(results):
                for i,result_item in enumerate(current_result):
                    if output_item[0] == result_item[0]:
                        if output_item[1]:
                            current_result[i] = output_item
                        else:
                            results.remove(output_item)
                            results.add(result_item)

            if previous_operation == 'or':
                results = results.union(current_result)
            elif previous_operation == 'and':
                results = results.intersection(current_result)

            previous_operation = child.operation
        # print(list(results))

        return list(results)


class Destination_rule:
    def __init__(self, content, command : Optional[str]='move'):
        self.content : List[str|Tuple[str,str|None]] = content or []
        self.command = command

