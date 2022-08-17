from typing import List
import re
from classes import *

type_name_pattern = re.compile(r'^\s*\[(.+?)]')

def parse_inner_block(text):
    outer_rule_type = re.search(type_name_pattern, text.splitlines()[0])
    if outer_rule_type:
        outer_rule_type = outer_rule_type.group(1)
    else:
        outer_rule_type = 'regex'
     
    outer_rule = Input_rule(None, None, outer_rule_type, True)
    for line in text.splitlines():
        if re.search(r'^\[', line) or re.search(r'^\s*(}|{)', line):
            continue
        
        rule = parse_input(line)
        if rule:
            outer_rule.children.append(rule)

    return outer_rule

def parse_input(text):
    for line in text.splitlines():
        if re.search(r'^\[\[', line) or re.search(r'^\s*(}|{)', line):
            continue
        if re.search(r'^\[[^\[]', line):
            
            if not re.search('{', line):
                outer_rule_type = re.search(type_name_pattern, line)
                if outer_rule_type:
                    outer_rule_type = outer_rule_type.group(1)
                else:
                    outer_rule_type = 'regex'

                outer_rule_name = re.search(r'\[\[(.+?)]]\s*$', line)
                if outer_rule_name:
                    outer_rule_name = outer_rule_name.group(1)
                    line = re.sub(r'\[\[(.+?)]]\s*$', '', line)

                return Input_rule(outer_rule_name, re.sub(type_name_pattern, '', line).strip(), outer_rule_type, False)

            return parse_inner_block(text)
        
        rule_name = re.search(r'\[\[(.+?)]]\s*$', line)
        if rule_name:
            rule_name = rule_name.group(1)
            line = re.sub(r'\[\[(.+?)]]\s*$', '', line)

        destination_marker_match = re.search('->', line)
        if destination_marker_match:
            line = line[slice(None,destination_marker_match.span()[0])].strip()

        if not line:
            continue
            
        return Input_rule(rule_name, line, 'regex', False)

def parse_destination(text : str) -> Destination_rule:
    text_list = re.split(r'(?={)|(?<=})', text)

    destination_rule = Destination_rule(None)
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


def parse_whole_content(text) -> List[Block]:
    blocks : List[Block] = []
    input_rule_regex = re.compile(r'(?P<action>\[[^\[\]]+\]\s*)?(((?P<regex>[^{\s][^\[\]\s]+\s*))?(?P<name>\[\[.+]]\s*)|(?P<regex2>((?<=])|^)\s*[^{\s\[\]][^\[\]\s]+\s*)|\[.+\]\s*\{\n(.+?\n\n*)+\s*})(?P<operator>\band\b)?$')

    for m in re.finditer(r'(\A|^)([\S].+?[\S])(\Z|\n$)', text, re.DOTALL | re.MULTILINE):
        block_text = m.group(2)

        root_path = './'

        set_name = re.search(r'^\[\[.+]]$', block_text.splitlines()[0])

        input_rule_set = Rule_set(set_name, None)
        destination_rule_set = Destination_set(None)


        is_on_destination_section = False
        cached_lines = 0
        for i,line in enumerate(block_text.splitlines()):

            if is_on_destination_section == False:
                if cached_lines>0:
                    cached_lines-=1
                    continue

                if re.search(r'^\[[^\[]', line):
                    if not re.search('{', line):
                        rule = parse_input(line)
                        if rule:
                            rule.root = root_path
                            input_rule_set.children.append(rule)
                        continue

                    inner_block_lines = ''
                    open_brackets = 0
                    
                    for inner_line in text.splitlines()[i+1:]:
                        inner_block_lines += f'{inner_line}\n'
                        open_brackets -= len(re.findall('}', inner_line))
                        open_brackets += len(re.findall('{', inner_line))
                        
                        if open_brackets <= 0:
                            break
                        cached_lines+=1
                    
                    rule = parse_input(inner_block_lines)
                    if rule:
                        rule.root = root_path
                        input_rule_set.children.append(rule)
                    continue

                rule = parse_input(line)
                if rule:
                    rule.root = root_path
                    input_rule_set.children.append(rule)
            else:
                destination_rule_set.children.append(parse_destination(line))

            destination_marker_match = re.search('->', line)
            if destination_marker_match:
                is_on_destination_section = True
                line = line[slice(destination_marker_match.span()[1],None)].strip()
                destination_rule_set.children.append(parse_destination(line))
                
        block = Block(input_rule_set, destination_rule_set)

        input_rule_set.root = root_path
        blocks.append(block)

        # for rule in input_rule_set.children:
            # print(rule.children)
            # print('-----')
        # for rule in destination_rule_set.children:
            # print(rule.content)
            # print('-----')

    # for block in blocks:
        # for child in block.destination_set.children:
            # print(child.content)
        
    return blocks

