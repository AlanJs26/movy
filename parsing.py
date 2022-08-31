from typing import List, Union,Dict,Any
import re
from classes import *
from rich import print

type_name_pattern = re.compile(r'^\s*\[(.+?)]')
block_regex = re.compile(r'\[(?P<action>.+)\].+{\s*\n(?P<content>(.+\n\n*)+)\s*}')
input_rule_regex = re.compile(r'(?P<action>\[[^\[\]]+\]\s*)?(((?P<regex>[^{\s][^\[\]\n]+?\s*))?(?P<name>\[\[.+]]\s*)|(?P<regex2>((?<=[^\]]])|^)\s*[^{\s\[\]][^\[\]\n]+?\s*[^{])|(?P<block>\[.+?\]\s*([^\s]*)\s*\{\n((.+?\n\n*)+)\s*}))(?P<operator>\b(and|or)\b)?$', flags=re.MULTILINE)

def parse_inner_block(text):

    outer_rule_match = re.search(block_regex, text)
    if outer_rule_match:
        outer_rule_match = outer_rule_match.groupdict()
        outer_rule_action = outer_rule_match['action'] or 'regex'
        outer_rule_content = outer_rule_match['content']
    else:
        print("[red]Error")
        return Input_rule(None, text, None, False)
     
    outer_rule = Input_rule(None, None, outer_rule_action, True)


    input_rule_matches = re.finditer(input_rule_regex, outer_rule_content)

    for input_match in input_rule_matches:
        dictgroups = input_match.groupdict()
        outer_rule.children.append(parse_match(dictgroups))

    return outer_rule

def parse_match(rule_match:Dict[str,Union[str,Any]]):

    rule_regex = rule_match['regex'].strip() if rule_match['regex'] else 'regex'
    if rule_match['regex2']:
        rule_regex = rule_match['regex2'].strip()
    rule_action = rule_match['action']
    rule_name = rule_match['name']
    if rule_name:
        rule_name = rule_name.strip()[2:-2].strip()
    if rule_action:
        rule_action = rule_action.strip()[1:-1].strip()

    if rule_match['block']:
        return parse_inner_block(rule_match['block'].strip())

    rule = Input_rule(rule_name, rule_regex, rule_action, False)

    if rule_match['operator']:
        rule.operation = rule_match['operator']

    return rule

def parse_destination(text : str) -> Union[Destination_rule,None]:
    text = text.replace('->', '').strip()
    destination_match = re.search(r'(\[(?P<command>.+?)\]\s*)?(?P<content>.+)', text)
    if not destination_match:
        return None

    command_name = destination_match.group('command') or 'move'
    content = destination_match.group('content')

    text_list = re.split(r'(?={)|(?<=})', content)

    destination_rule = Destination_rule(None, command_name)
    for item in text_list:
        if not item:
            continue
        if item.find('{') != -1:
            item = item[1:-1]
            group_split = item.split('|')
            if len(group_split) > 1:
                pattern_name, action_name, *_ = group_split
            else:
                pattern_name = group_split[0]
                action_name = None

            destination_rule.content.append((pattern_name,action_name))
            continue

        destination_rule.content.append(item)

    return destination_rule


def parse_whole_content(text, root_path : Optional[str] = './') -> List[Block]:
    blocks : List[Block] = []

    count = 1
    for m in re.finditer(r'(\A|^)([\S].+?[\S])(\Z|\n$)', text, re.DOTALL | re.MULTILINE):
        block_text = m.group(2)

        set_name = re.search(r'^\[\[(.+)]]$', block_text.splitlines()[0])
        if set_name:
            set_name = set_name.group(1)
        else:
            set_name = ''


        input_rule_set = Rule_set(set_name or f'block_{count}', None)
        destination_rule_set = Destination_set(None)

        if set_name:
            block_text = '\n'.join(block_text.splitlines()[1:])

        text_split = block_text.split('->', 1)

        if not len(text_split):
            continue

        input_section_text = text_split[0]

        input_rule_matches = re.finditer(input_rule_regex, input_section_text)

        for input_match in input_rule_matches:
            group_dict = input_match.groupdict()
            # print(group_dict)
            input_rule_set.children.append(parse_match(group_dict))

        block = Block(input_rule_set, destination_rule_set)
        if len(text_split) >= 2:
            destination_section_text = text_split[1]
            for destination_line in destination_section_text.splitlines():
                block.destination_set.children.append(parse_destination(destination_line))
        else:
            count-=1
            block.type = 'routine'
                

        input_rule_set.root = root_path
        blocks.append(block)
        count += 1

        
    return blocks

