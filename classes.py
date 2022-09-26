from typing import List, Optional, Tuple,Callable, Union
import os
from datetime import datetime
import re
from rich import print as rprint
from utils import check_ext, get_file_content, mergedicts

def parse_action(text:str, action_type:str, pattern_string : Optional[str] = None, flags=re.MULTILINE, rule = None) -> Tuple[str,bool]:
    new_text = ''
    non_text_transformers = ['template']
    not_string_valid = ['filecontent']
    action_results = {}
    options = {}

    def get_rule_options(options:dict, rule):

        if type(rule.action_content) == list:
            for opt_key, action_arg in zip(options.keys(), rule.action_content):
                if type(action_arg) == str and action_arg.isnumeric():
                    options[opt_key] = int(action_arg)
                else:
                    options[opt_key] = action_arg

        children_dict = rule.get_children_as_dict()
        for key, child_dict in children_dict.items():
            if key in options:
                if type(child_dict['content']) == str and child_dict['content'].isnumeric():
                    options[key] = int(child_dict['content'])
                else:
                    options[key] = child_dict['content']
        
        return options
    
    if action_type == 'regex':
        new_text = text
    elif action_type == 'extension':
        new_text = os.path.splitext(text)[1].replace('.', '')
    elif action_type == 'filecontent':
        valid_extensions = ['pdf', 'txt', 'csv', 'c', 'cpp', 'dat', 'log', 'xml', 'js', 'jsx', 'py', 'html', 'sh']
        if os.path.splitext(text)[1].replace('.', '') in valid_extensions:
            options = {
                'maxlines': 10,
                'linelength': 200,
                'verbose': 'false'
            }

            options = get_rule_options(options, rule)

            new_text = get_file_content(text, options['maxlines'], options['linelength'])
    elif action_type == 'basename':
        new_text = os.path.splitext(os.path.basename(text))[0]
    elif action_type == 'template' and check_ext(text, 'pdf'):
        pattern_string = pattern_string.strip() if pattern_string else None
        if rule and (not pattern_string or re.search(pattern_string, text, flags=flags)):
            # return '', True, action_results
            from similarity import pdf_similarity

            options = {
                'path': '',
                'threshold': 70,
                'verbose': 'false'
            }

            options = get_rule_options(options, rule)
            
            if check_ext(options['path'], 'pdf'):
                score = pdf_similarity(options['path'], text)
                # print([text, score*100, score*100 > options['threshold'], pattern_string])
                # print('.')
                if options['verbose'] == 'true':
                    rprint(f'[cyan]template[white] -> [blue]path: [white]{options["path"]} [blue]filepath:[white] {text} [{"green" if score*100 > options["threshold"] else "red"}]score: [white]{score*100:.2f}')

                return '', score*100 > int(options['threshold']), action_results

    if pattern_string is not None and action_type not in non_text_transformers:
        try:
            text_match = re.search(pattern_string, new_text, flags = flags)
        except:
            print(pattern_string)
            text_match = None

        if text_match:
            matchdict = text_match.groupdict()
            matchgroups = text_match.groups()

            if not hasattr(action_results, action_type):
                action_results[action_type] = {}

            if action_type not in not_string_valid:
                action_results[action_type]['string'] = text_match.string
            else:
                action_results[action_type]['string'] = ''
            
            if (len(matchdict) or len(matchgroups)) and not hasattr(action_results, action_type):
                action_results[action_type]['groups'] = {}

            if len(matchdict):
                action_results[action_type]['groups'] = { **action_results[action_type]['groups'], **text_match.groupdict() }
            if len(matchgroups):
                action_results[action_type]['groups'] = { **action_results[action_type]['groups'], **dict(zip(range(1,len(matchgroups)+1), matchgroups)) }
            

            # if len(action_results):
                # print(action_results)
        match_result = bool(text_match)

        if action_type == 'filecontent' and 'verbose' in options and options['verbose'] == 'true':
            rprint(f'[cyan]filecontent [white]-> [blue]pattern: [white]{pattern_string} [blue]match: {"[green]true" if match_result else "[red]false"}')
            print(new_text)

        return '', match_result, action_results

    if new_text:
        return new_text, True, action_results

    return text, False, action_results


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

            if (type(rule.action_content) == str and current_time == rule.action_content.strip()) or rule.action_content == None: 
                blocks_pending.append(current_block)

        return blocks_pending

def parse_placeholder(destination_item, input_match):
    dest_action,dest_name = destination_item

    command_match = re.search(r'((?P<command>\w+)\( *)?(?P<content>[\w\.]+)( *\))?', dest_action).groupdict()

    if command_match['content'] is None:
        return None

    new_text = ''
    dest_action_split = command_match['content'].split('.')

    if len(dest_action_split) > 1:
        if dest_action_split[1] == 'groups':
            try:
                if dest_action_split[2].isnumeric():
                    dest_action_split[2] = int(dest_action_split[2])
                new_text = input_match[2][dest_action_split[0]]['groups'][dest_action_split[2]]
            except:
                return None
    elif command_match['content'] in input_match[2]:
        new_text = input_match[2][command_match['content']]['string']

    if new_text:
        if command_match['command'] is not None:
            if command_match['command'] == 'lowercase':
                new_text = new_text.lower()
            elif command_match['command'] == 'uppercase':
                new_text = new_text.upper()
            elif command_match['command'] == 'titlecase':
                new_text = new_text.title()
        
        return new_text

    parsed_action_text, parse_status, _ = parse_action(input_match[0], dest_action)
    if parse_status == False:
        return None

    return parsed_action_text

class Destination_set:
    def __init__(self, children) -> None:
        self.children : List[Destination_rule] = children or []

    def eval_children(self, input_rule_results: List[Tuple[str,Union[None,str]]]):
        results = []
        # input_rule_results : list[Destination_rule]


        for input_match in input_rule_results:
            command_name = 'move'

            for child in self.children:
                command_name = child.command

                # input match
                # path, name, action_action_options

                # destination_item
                # List[str,Tuple[action:str,name:str]]

                inner_output = ""
                for destination_item in child.content:
                    dest_name = destination_item[1]
                    if isinstance(destination_item, str):
                        inner_output += destination_item
                    elif dest_name is None or dest_name == input_match[1]: # group name
                        parsed_text = parse_placeholder(destination_item, input_match)

                        if parsed_text:
                            inner_output += parsed_text
                        else:
                            break
                    else:
                        break
                else:
                    results.append((input_match[0], inner_output, command_name))
                    break
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
        elif '|' in self.action_type:
            action_split = self.action_type.strip().split('|')

            self.action_type = action_split[0]
            self.action_content = action_split[1:]

    
    def eval(self, root:Union[str, None]=None, file_paths:Union[List[str], None]=None):
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

        if file_paths:
            for file in file_paths:
                _, parse_status, action_results = parse_action(file, self.action_type, pattern_string, flags = pattern_flags, rule=self)

                if parse_status:
                    results.append(( file, self.name, action_results))
        else:
            for file in os.listdir(root):
                _, parse_status, action_results = parse_action(root+'/'+file, self.action_type, pattern_string, flags = pattern_flags, rule=self)

                if parse_status:
                    results.append(( root+'/'+file, self.name, action_results))

        return results
    
    def get_children_as_dict(self) -> dict:
        children_dict = {}

        for i, child in enumerate(self.children):
            children_dict[child.action_type] = {
                'content': child.content,
                'action_content': child.action_content,
                'index': i
            }

        return children_dict
    
class Rule_set:
    def __init__(self, name : str, children : Union[List[Input_rule],None]) -> None:
        self.name = name
        self.children = children or []
        self.root : None|str = None

    def eval_children(self):
        final_results = []
        or_final_results = []
        previous_operation = 'or'


        for child in self.children:
            final_path_list = [x[0] for x in final_results]
            final_results_len = len(final_path_list)

            if previous_operation == 'and':
                if len(final_path_list):
                    current_results = child.eval(self.root, final_path_list)
                else:
                    current_results = []
            else:
                current_results = child.eval(self.root)

            current_path_list = [x[0] for x in current_results]

            # rprint(current_results)

            if previous_operation == 'or':
                # same_items = [x for x in current_results if x[0] in final_path_list]
                final_results.extend(x for x in current_results if x[0] not in final_path_list)
                for result_item in current_results:
                    path, name, action_options = result_item

                    for i in range(final_results_len):
                        final_path, final_name, final_action_options = final_results[i]

                        if final_path == path and (name is not None or final_name is None):
                            final_results[i] = (path, name, dict(mergedicts(final_action_options, action_options)))
                        else:
                            final_results[i] = (final_path, final_name, dict(mergedicts(final_action_options, action_options)))

            elif previous_operation == 'and':
                final_results = [x for x in final_results if x[0] in current_path_list]

                # print('-----')
                # count = 0
                # rprint(final_results)
                for i,final_item in enumerate(final_results):
                    final_path, final_name, final_action_options = final_item

                    for result_item in current_results:
                        path, name, action_options = result_item

                        if path == final_path and (name is not None or final_name is None): # keep the last named group 
                            # count+=1
                            # print(name)
                            final_results[i] = (path, name, dict(mergedicts(final_action_options, action_options)))
                        # else:
                            # final_results[i] = (final_path, final_results[i][1], dict(mergedicts(final_action_options, action_options)))
                # if count:
                #     print(count)
                #     rprint(current_results)
                #     rprint(final_results)


            or_final_path_list = [x[0] for x in or_final_results]
            if previous_operation == 'and' and child.operation == 'or':
                or_final_results.extend(x for x in final_results if x[0] not in or_final_path_list)
                final_results = []
            previous_operation = child.operation

        or_final_results.extend(x for x in final_results if x[0] not in or_final_path_list)

        # print('final_results ---------')
        # rprint(or_final_results)
        # print(final_results)

        return list(or_final_results)


class Destination_rule:
    def __init__(self, content, command : Optional[str]='move'):
        self.content : List[str|Tuple[str,str|None]] = content or []
        self.command = command

