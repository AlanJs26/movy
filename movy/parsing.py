from .classes import *
import re
from rich import print as rprint
import yaml
from typing import Optional, List, Tuple
from dataclasses import dataclass
from copy import deepcopy
from .rules import RULES
from .actions import ACTIONS


class SyntaxError(Exception):
    def __init__(self, message:str, file:Optional[str]=None, lineno: Optional[int]=None, content:Optional[str]=None):
        self.file = file
        self.lineno = lineno
        self.content = content
        self.message = message

    def __str__(self):
        output = '[red]'
        if self.file:
            output += f'File: {self.file}, '
        if self.lineno:
            output += f'line: {self.lineno}'

        return f'''{output}
[white]{self.content}

[red]SyntaxError: {self.message}
'''

@dataclass
class CommandToken():
    command: str
    children: list['CommandToken']

    def _copy(self):
        new_command = deepcopy(self)

        if not new_command.children:
            return new_command

        new_command.children = [child._copy() for child in new_command.children]

        return new_command
            

    def flat_children(self):
        flat_children:list['CommandToken'] = self._copy().children

        offset = 1
        for i,child in enumerate(self.children):
            for inner_child in child.flat_children():
                flat_children.insert(i+offset, inner_child)
                offset += 1
                
        for child in flat_children:
            for inner_child in flat_children:
                if inner_child in child.children:
                    child.children.remove(inner_child)

        return flat_children
    

@dataclass
class ExpressionToken():
    content: str


@dataclass
class ArgumentToken():
    name: str
    content: list[str|ExpressionToken]

    @staticmethod
    def regex():
        return re.compile(r'^[A-Za-z ]*:')


@dataclass
class RuleToken():
    name: str
    operator: str
    content: list[str|ExpressionToken]
    arguments: list[ArgumentToken]
    flags: list[str]

    def __post_init__(self):
        if self.operator and self.operator not in Input_rule.valid_operators:
            raise SyntaxError(message=f'Unknown operator: {self.operator}')

    @staticmethod
    def regex():
        return re.compile(r'^[\(\)A-Za-z ]*:')

@dataclass
class ActionToken():
    operator: str
    name: str
    content: list[str|ExpressionToken]
    arguments: list[ArgumentToken]

    def __post_init__(self):
        if self.operator and self.operator not in Destination_rule.valid_operators:
            raise SyntaxError(message=f'Unknown operator: {self.operator}')

    @staticmethod
    def regex():
        return re.compile(r'^[\(\)A-Za-z ]*->')


class Document:
    def __init__(self, file:str):
        self.blocks: List[Block] = [] 
        self.root = os.getcwd()
        self.metadata: dict = {}
        self.file = file

        with open(file,'r', encoding='utf-8') as f:
            self.content = f.read()
            self.load(self.content)


    def load(self, content: str):
        try:
            content = self._remove_comments(content)
            content = self._parse_metadata(content)

            if 'root' in self.metadata:
                self.root = self.metadata['root']

            block_strings = self._split_blocks(content)

            for block_string in block_strings:
                content, name = self._parse_block_name(block_string)

                block = Block(name)

                content = self._remove_empty_lines(content)

                grouped_commands = self._group_brackets(content)
                grouped_actions = self._group_actions(grouped_commands)
                commands = self._parse_commands(grouped_actions)

                # print('------')
                # rprint(commands)
                for command in commands:
                    if isinstance(command, RuleToken):
                        if command.name not in RULES:
                            raise Exception('Unknown rule')

                        block.commands.append(
                            RULES[command.name](
                                name=command.name,
                                operator=command.operator,
                                content=self._convert_expressions(command.content),
                                arguments=self._convert_arguments(command.arguments),
                                flags=command.flags
                            )
                        )
                    else:
                        if command.name not in ACTIONS:
                            raise Exception('Unknown action')
                        block.commands.append(
                            ACTIONS[command.name](
                                name=command.name,
                                content=self._convert_expressions(command.content),
                                arguments=self._convert_arguments(command.arguments),
                                operator=command.operator
                            )
                        )

                self.add_block(block)


                # print(content)
            # print(block_strings)
        except SyntaxError as e:
            rprint(str(e))

    def _convert_arguments(self, items: list[ArgumentToken]) -> list[Argument]:
        def convert(item: ArgumentToken) -> Argument:
            return Argument(item.name, self._convert_expressions(item.content))

        return list(map(convert, items))

    def _convert_expressions(self, items: list[str|ExpressionToken]) -> list[str|Expression]:
        def convert(item: str|ExpressionToken) -> str|Expression:
            if isinstance(item, str):
                return item
            return Expression(item.content)

        return list(map(convert, items))

    def _parse_commands(self, raw_commands:List[CommandToken]) -> list[RuleToken|ActionToken]:
        action_regex = ActionToken.regex()
        rule_regex = RuleToken.regex()

        
        commands:list[RuleToken|ActionToken] = []

        for raw_command in raw_commands:
            if re.search(rule_regex, raw_command.command):
                try:
                    commands.append(self._parse_rule(raw_command))
                except SyntaxError as e:
                    raise SyntaxError(message=e.message, file=self.file, lineno=self._find_line(raw_command.command),content=raw_command.command)
            elif re.search(action_regex, raw_command.command):
                try:
                    commands.append(self._parse_action(raw_command))
                except SyntaxError as e:
                    raise SyntaxError(message=e.message, file=self.file, lineno=self._find_line(raw_command.command),content=raw_command.command)
            else:
                raise SyntaxError(message='Unknown command', file=self.file, lineno=self._find_line(raw_command.command),content=raw_command.command)

        return commands

    def _parse_expressions(self, raw_commands:list[CommandToken], invert=False):
        expressions:list[str|ExpressionToken] = []
        for item in raw_commands:
            if item.children and invert:
                expressions.append(item.command)
                expressions.extend(ExpressionToken(content=child.command) for child in item.flat_children())
            elif item.command and not item.children and not invert:
                expressions.append(ExpressionToken(content=item.command))
            else:
                expressions.append(item.command)
                expressions.extend(self._parse_expressions(item.children))

        return expressions

    def _parse_argument(self, raw_command:CommandToken) -> ArgumentToken:
        rule_split = raw_command.command.split(':')
        rule_start = rule_split[0]

        rule_content:list[str|ExpressionToken] = [rule_split[1]]

        rule_content.extend(self._parse_expressions(raw_command.children))

        return ArgumentToken(name=rule_start, content=rule_content)
            

    def _parse_rule(self, raw_command:CommandToken) -> RuleToken:
        rule_split = raw_command.command.split(':', 1)

        # Parse Commands
        rule_content:list[str|ExpressionToken] = [rule_split[1]]
        rule_arguments: list[CommandToken] = []

        if len(raw_command.children) == 1:
            rule_arguments = raw_command.children
        elif raw_command.children:
            rule_arguments = raw_command.children[-1].children
            raw_command.children[-1].children = []

            raw_command.children[0] = CommandToken('',children=[raw_command.children[0]]) 
            rule_content.extend(self._parse_expressions(raw_command.children, invert=True))

        # Parse Arguments
        parsed_arguments:list[ArgumentToken] = []

        prev:Optional[ArgumentToken] = None
        for argument in rule_arguments:
            if re.search(ArgumentToken.regex(), argument.command):
                prev=self._parse_argument(argument)
                parsed_arguments.append(prev)
            elif prev:
                prev.content.append(argument.command)
                for child in argument.flat_children():
                    prev.content.append(ExpressionToken(child.command))
            else:
                raise SyntaxError(message='Invalid Argument', file=self.file, lineno=self._find_line(argument.command),content=argument.command)
                
        rule_start = rule_split[0].strip()
        rule_name = rule_start.split(' ')[-1]


        rule_start = ' '.join(rule_start.split(' ')[:-1])

        # Parse Flags
        flags_regex = re.compile(r'\((.+?)\)')
        rule_flags = []
        for flag in re.finditer(flags_regex, rule_start):
            rule_flags.append(flag.group(1))

        rule_start = re.sub(flags_regex, '', rule_start)
        rule_operator = rule_start.strip()

        # Remove empty strings
        rule_content = list(filter(lambda x:x, rule_content))
        parsed_arguments = list(filter(lambda x:x, parsed_arguments))

        if any('->' in item for item in rule_content if isinstance(item, str)):
            raise SyntaxError(message='Actions and rules must be in different lines', file=self.file, lineno=self._find_line(raw_command.command),content=raw_command.command)
        

        return RuleToken(flags=rule_flags, operator=rule_operator, name=rule_name, content=rule_content, arguments=parsed_arguments)

    def _parse_action(self, raw_command:CommandToken) -> ActionToken:
        rule_split = raw_command.command.split('->', 1)

        # Parse Commands
        rule_content:list[str|ExpressionToken] = [rule_split[1]]
        rule_arguments: list[CommandToken] = []

        # rprint(raw_command)
        if len(raw_command.children) == 1 and re.search(ArgumentToken.regex(), raw_command.children[0].command):
            rule_arguments = raw_command.children
        elif raw_command.children:
            if not re.search(ArgumentToken.regex(), raw_command.children[0].command):
                rule_arguments = raw_command.children[-1].children

                raw_command.children[-1].children = []

                raw_command.children[0] = CommandToken('',children=[raw_command.children[0]]) 
                rule_content.extend(self._parse_expressions(raw_command.children, invert=True))
            else:
                rule_arguments = raw_command.children

        # Parse Arguments
        parsed_arguments:list[ArgumentToken] = []

        prev:Optional[ArgumentToken] = None
        for argument in rule_arguments:
            if re.search(ArgumentToken.regex(), argument.command):
                prev=self._parse_argument(argument)
                parsed_arguments.append(prev)
            elif prev:
                prev.content.append(argument.command)
                for child in argument.flat_children():
                    prev.content.append(ExpressionToken(child.command))
            else:
                raise SyntaxError(message='Invalid Argument', file=self.file, lineno=self._find_line(argument.command),content=argument.command)
                
        rule_start = rule_split[0].strip()

        rule_operator = ''
        rule_split = []
        for name in rule_start.split(' '):
            if name in Destination_rule.valid_operators and not rule_operator:
                rule_operator = name
                continue
            rule_split.append(name)

        rule_name = rule_split[-1] if rule_split else ''


        # Parse Flags
        flags_regex = re.compile(r'\((.+?)\)')
        if any(re.finditer(flags_regex, rule_start)):
            raise SyntaxError(message="Isn't possible to attach flags to actions", file=self.file, lineno=self._find_line(rule_start),content=rule_start)



        # Remove empty strings
        rule_content = list(filter(lambda x:x, rule_content))
        parsed_arguments = list(filter(lambda x:x, parsed_arguments))



        return ActionToken(operator=rule_operator, name=rule_name, content=rule_content, arguments=parsed_arguments)
        # return RawAction(operator='and', name='basename', content=['fatura'], arguments=[Argument('old', ['jose'])])

    def _group_actions(self, commands:List[CommandToken]) -> List[CommandToken]:
        action_regex = ActionToken.regex()
        rule_regex = RuleToken.regex()

        prev:Optional[CommandToken] = None
        grouped:List[CommandToken] = []
        for item in commands:
            if re.search(rule_regex, item.command):
                prev = item
                grouped.append(item)
                continue
            if re.search(action_regex, item.command):
                grouped.append(item)
                prev = item
                continue

            if not prev:
                grouped.append(item)
                continue

            prev.children.append(item)
        
        return grouped

    def _group_brackets(self, content):
        content_split = content.split('\n')
        # content_split = re.split(r'\n|(?=->)', content)

        def split_with_delimiter(content:str, delimiter:str):
            content_list = []
            for item in content.split(delimiter):
                content_list.append(item)
                content_list.append(delimiter)

            return content_list[:-1]
        
        def get_deepest_child(raw_command: CommandToken):
            if raw_command.children:
                return get_deepest_child(raw_command.children[-1])
            else:
                return raw_command

        content_split = [ new_item for substring in content_split for new_item in split_with_delimiter(substring, '{') ]
        content_split = [ new_item for substring in content_split for new_item in split_with_delimiter(substring, '}') ]
        content_split = list(filter(lambda x: x, content_split))

        nest_stack:List[CommandToken] = []
        grouped:List[CommandToken] = []
        for item in content_split:
            if item == '{':
                prev = grouped[-1]
                nest_stack.append(get_deepest_child(prev))
                continue
            if item == '}':
                if len(nest_stack) == 0:
                    raise SyntaxError(message='Mismatched bracket', file=self.file, lineno=self._find_line(grouped[-1].command),content=content)
                nest_stack.pop()
                continue

            if len(nest_stack) == 0:
                grouped.append(CommandToken(command=item.rstrip(), children=[]))
                continue

            nest_stack[-1].children.append(CommandToken(command=item.rstrip(), children=[]))

        if len(nest_stack) > 0:
            raise SyntaxError(message='Mismatched bracket', file=self.file, lineno=self._find_line(nest_stack[-1].command),content=content)
        
        return grouped


    def _remove_empty_lines(self, content:str) -> str:
        empty_lines_regex = re.compile(r'^\s*$\n', flags=re.MULTILINE)

        return re.sub(empty_lines_regex, '', content)

    def _find_line(self, query:str):

        match = self.content.find(query)

        if match == -1:
            return 0

        substring = self.content[:match]
        return substring.count('\n')

    def _parse_block_name(self, content:str) -> Tuple[str,str]:
        block_name_regex = re.compile(r'\[\[(.+?)\]\]')

        match = re.search(block_name_regex, content)
        if not match:
            return content, ''

        name = match.group(1).strip()

        if not re.search(r'^[A-Za-z ]+$', name):
            raise SyntaxError(message='Block name in wrong format (only letters)', file=self.file, lineno=self._find_line(match.group(0)),content=match.string)

        content = re.sub(block_name_regex, '', content)

        return content, name

    def _split_blocks(self, content:str) -> List[str]:
        blocks_regex = re.compile(r'\S.+?(?=\[\[.+?]]|\Z)', flags=re.DOTALL|re.MULTILINE)

        matches = re.findall(blocks_regex,content)

        if not matches:
            raise SyntaxError(message='Empty file', file=self.file, lineno=0,content='')

        return [item.strip() for item in matches]

    def _remove_comments(self, content:str) -> str:
        content = re.sub(r'(\n^)?#.*', '', content)

        return content

    def _parse_metadata(self, content:str) -> str:
        metadata_regex = re.compile(r'(?P<start>\A[\s]+|\A)?-{3,}[\s]*$(?P<metadata>.+?)-{3,}[\s]*$', flags=re.DOTALL|re.MULTILINE)

        match = re.search(metadata_regex, content)

        if not match:
            return content

        match_dict = match.groupdict()

        if match_dict['start'] is None:
            span = (match.pos, match.pos+len(match_dict['metadata']))
            error_string = "\n".join(content.splitlines()[span[0]:span[1]])
            raise SyntaxError(message='Metadata must be at the start of the file', file=self.file, lineno=span[0],content=error_string)

        metadata = match_dict['metadata'].strip()

        self.metadata = yaml.load(metadata, yaml.BaseLoader)
        
        return re.sub(metadata_regex, '', content)

    def add_block(self, block: Block):
        block.root = self.root

        self.blocks.append(block)

    def pretty_print(self):
        for block in self.blocks:
            rprint(block.__str__())

    def run_blocks(self):
        history = FileHistory()
        for block in self.blocks:
            rprint(f'[green]evaluating [blue]{block.name}')
            block.eval(history)

if __name__ == '__main__':
    document = Document('./scripts/first.movy')
    document.pretty_print()
    print('-------------')
    document.run_blocks()
