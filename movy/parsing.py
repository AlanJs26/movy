from .classes import *
import re
from rich import print as rprint
import yaml
from typing import Optional, List, Tuple
from dataclasses import dataclass,field
from .rules import RULES
from .actions import ACTIONS
from rich.rule import Rule
from rich.panel import Panel


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
class BracketToken():
    content: list['str|BracketToken']
    raw:str=''
    type:str = 'bracket'

    def to_string(self) -> str:
        output = ''
        for item in self.content:
            if isinstance(item, str):
                output += item
            else:
                output += item.to_string()
        return output

@dataclass
class ExpressionToken():
    content: str


    @staticmethod
    def regex():
        return re.compile(r'^[A-Za-z_ ]*:')


@dataclass
class ArgumentToken():
    name: str
    content: list[str|ExpressionToken]


@dataclass
class CommandToken():
    command: str
    children: list['BracketToken|str']
    raw:str=''
    type:str = 'string'
    arguments: list[ArgumentToken] = field(default_factory=lambda: [])

    def __post_init__(self):
        if not self.raw:
            self.raw = self.command


@dataclass
class RuleToken():
    name: str
    operator: list[str]
    content: list[str|ExpressionToken]
    arguments: list[ArgumentToken]
    flags: list[str]

    def __post_init__(self):
        for op in self.operator:
            if op not in Input_rule.valid_operators:
                raise SyntaxError(message=f'Unknown operator: {op}')

    @staticmethod
    def regex():
        return re.compile(r'^[\(\)A-Za-z_ ]*:')

@dataclass
class ActionToken():
    operator: list[str]
    name: str
    content: list[str|ExpressionToken]
    arguments: list[ArgumentToken]

    def __post_init__(self):
        for op in self.operator:
            if op not in Destination_rule.valid_operators:
                raise SyntaxError(message=f'Unknown operator: {op}')

    @staticmethod
    def regex():
        return re.compile(r'^[\(\)A-Za-z_ ]*->')


class Document:
    def __init__(self, file:Optional[str]=None, text:Optional[str]=None):
        if not file and not text:
            raise Exception('You must specify which file to open')

        self.blocks: List[Block] = [] 
        self.root = os.getcwd()
        self.metadata: dict = {}
        if file:
            self.file = file
            with open(file,'r', encoding='utf-8') as f:
                self.content = f.read()
        elif text:
            self.file = 'None'
            self.content = text

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

                if 'ignore_all_exceptions' in self.metadata:
                    ignore_all_exceptions = bool(self.metadata['ignore_all_exceptions'])
                else:
                    ignore_all_exceptions = False

                block.ignore_all_exceptions = ignore_all_exceptions


                content = self._remove_empty_lines(content)

                grouped_commands = self._group_brackets(content)
                grouped_actions = self._group_actions(grouped_commands)
                commands = self._parse_commands(grouped_actions)

                # print('------grouped_commands')
                # rprint(grouped_commands)
                # print('------grouped_actions')
                # rprint(grouped_actions)
                # print('------commands')
                # rprint(commands)
                # print('----')
                for command in commands:
                    if isinstance(command, RuleToken):
                        if command.name not in RULES:
                            raise SyntaxError(message='Unknown rule', file=self.file, lineno=self._find_line(self._squash_expressionstokens(command.content)), content=command.name)

                        if 'ignore_exceptions' in self.metadata:
                            ignore_exceptions = self.metadata['ignore_exceptions']
                        else:
                            ignore_exceptions = False

                        block.commands.append(
                            RULES[command.name](
                                name=command.name,
                                operator=command.operator,
                                content=self._convert_expressions(command.content, ignore_exceptions),
                                arguments=self._convert_arguments(command.arguments),
                                flags=command.flags,
                                ignore_all_exceptions=ignore_all_exceptions
                            )
                        )
                    else:
                        if command.name not in ACTIONS:
                            raise SyntaxError(message='Unknown action', file=self.file, lineno=self._find_line(self._squash_expressionstokens(command.content)), content=command.name)

                        if 'ignore_exceptions' in self.metadata:
                            ignore_exceptions = self.metadata['ignore_exceptions']
                        else:
                            ignore_exceptions = True

                        block.commands.append(
                            ACTIONS[command.name](
                                name=command.name,
                                content=self._convert_expressions(command.content, ignore_exceptions),
                                arguments=self._convert_arguments(command.arguments),
                                operator=command.operator,
                                ignore_all_exceptions=ignore_all_exceptions
                            )
                        )

                self.add_block(block)


                # print(content)
            # print(block_strings)
        except SyntaxError as e:
            rprint(str(e))
            self.blocks = []

    def _squash_expressionstokens(self, tokens: list[str|ExpressionToken]) -> str:
        output = ''
        for token in tokens:
            if isinstance(token, str):
                output += token
            else:
                output += token.content
        return output

    def _convert_arguments(self, items: list[ArgumentToken]) -> list[Argument]:
        def convert(item: ArgumentToken) -> Argument:
            return Argument(item.name.strip(), self._convert_expressions(item.content))

        return list(map(convert, items))

    def _convert_expressions(self, items: list[str|ExpressionToken], ignore_exceptions = False) -> list[str|Expression]:
        def convert(item: str|ExpressionToken) -> str|Expression:
            if isinstance(item, str):
                return item
            return Expression(item.content, ignore_exceptions)

        return list(map(convert, items))

    def _parse_commands(self, raw_commands:List[CommandToken]) -> list[RuleToken|ActionToken]:
        
        commands:list[RuleToken|ActionToken] = []

        for raw_command in raw_commands:
            if raw_command.type == 'rule':
                try:
                    commands.append(self._parse_rule(raw_command))
                except SyntaxError as e:
                    raise SyntaxError(message=e.message, file=self.file, lineno=self._find_line(raw_command.command),content=raw_command.command)
            elif raw_command.type == 'action':
                try:
                    commands.append(self._parse_action(raw_command))
                except SyntaxError as e:
                    raise SyntaxError(message=e.message, file=self.file, lineno=self._find_line(raw_command.command),content=raw_command.command)
            else:
                raise SyntaxError(message='Unknown command', file=self.file, lineno=self._find_line(raw_command.command),content=raw_command.command)

        return commands

    def _parse_expression(self, token:BracketToken):
        return ExpressionToken(token.to_string())

    def _parse_argument(self, raw_command:BracketToken) -> list[ArgumentToken]:
        if isinstance(raw_command.content[0], BracketToken):
            raise Exception('invalid argument')

        prev:Optional[ArgumentToken] = None
        grouped:List[ArgumentToken] = []
        for token in raw_command.content:

            if isinstance(token, str):
                split = token.split(':', 1)
                if len(split) != 2:
                    raise Exception('invalid argument name')
                prev = ArgumentToken(split[0], [split[1]])
                grouped.append(prev)
                continue

            if not prev:
                raise Exception('invalid argument format')

            if isinstance(token, BracketToken):
                if token.type == 'argument':
                    raise Exception('you cannot nest arguments')

                prev.content.append(self._parse_expression(token))

        return grouped
            

    def _parse_rule(self, raw_command:CommandToken) -> RuleToken:

        # Parse Commands
        rule_content:list[str|ExpressionToken] = []

        for item in raw_command.children:
            if isinstance(item, BracketToken):
                rule_content.append(self._parse_expression(item))
            else:
                rule_content.append(item)

        rule_name = raw_command.command.rstrip().split()[-1]


        rule_start = ' '.join(raw_command.command.split()[:-1])

        # Parse Flags
        flags_regex = re.compile(r'\((.+?)\)')
        rule_flags = []
        for flag in re.finditer(flags_regex, rule_start):
            rule_flags.append(flag.group(1))

        rule_start = re.sub(flags_regex, '', rule_start)
        rule_operator = rule_start.strip().split()

        if any('->' in item for item in rule_content if isinstance(item, str)):
            raise SyntaxError(message='Actions and rules must be in different lines', file=self.file, lineno=self._find_line(raw_command.command),content=raw_command.command)

        return RuleToken(flags=rule_flags, operator=rule_operator, name=rule_name, content=rule_content, arguments=raw_command.arguments)

    def _parse_action(self, raw_command:CommandToken) -> ActionToken:
        # Parse Commands
        rule_content:list[str|ExpressionToken] = []

        for item in raw_command.children:
            if isinstance(item, BracketToken):
                rule_content.append(self._parse_expression(item))
            else:
                rule_content.append(item)

        rule_name = raw_command.command.rstrip().split()[-1]


        rule_start = ' '.join(raw_command.command.split()[:-1])

        rule_operator = rule_start.strip().split()


        # Parse Flags
        flags_regex = re.compile(r'\((.+?)\)')
        if any(re.finditer(flags_regex, rule_start)):
            raise SyntaxError(message="Isn't possible to attach flags to actions", file=self.file, lineno=self._find_line(rule_start),content=rule_start)



        # # Remove empty strings
        # rule_content = list(filter(lambda x:x, rule_content))
        # parsed_arguments = list(filter(lambda x:x, parsed_arguments))



        return ActionToken(operator=rule_operator, name=rule_name, content=rule_content, arguments=raw_command.arguments)
        # return RawAction(operator='and', name='basename', content=['fatura'], arguments=[Argument('old', ['jose'])])

    def _group_actions(self, tokens:List[BracketToken|str]) -> List[CommandToken]:
        action_regex = ActionToken.regex()
        rule_regex = RuleToken.regex()

        prev:Optional[CommandToken] = None
        grouped:List[CommandToken] = []
        for item in tokens:
            if isinstance(item, str) and re.search(rule_regex, item):
                split = item.split(':', 1)
                prev = CommandToken(command=split[0], children=[split[1]] if split[1] else [], raw='', type='rule')
                grouped.append(prev)
                continue
            if isinstance(item, str) and re.search(action_regex, item):
                split = item.split('->', 1)
                prev = CommandToken(command=split[0], children=[split[1]] if split[1] else [], raw='', type='action')
                grouped.append(prev)
                continue

            if not prev:
                raise Exception('invalid command')

            if isinstance(item, BracketToken) and item.type == 'argument':
                prev.arguments = self._parse_argument(item)
            else:
                prev.children.append(item)
        
        return grouped

    def _tokenizer(self, content:str):

        def split_with_delimiter(content_list:list[str], pattern:str, delimiter:str): 
            count = 0
            tokens = content_list

            while count < len(tokens):
                tokens[count] = tokens[count].replace('\\'+pattern, '&&&&')
                split = re.split(pattern, tokens[count], 1)
                if len(split) > 1:
                    split.insert(1,delimiter)
                    tokens.remove(tokens[count])
                    tokens[slice(count,count)] = split

                    tokens[count] = tokens[count].replace('&&&&', pattern)

                    count += 2
                else:
                    tokens[count] = tokens[count].replace('&&&&', pattern)
                    count+=1

            return tokens
        
        tokens = [content]

        tokens = split_with_delimiter(tokens, r'{\n', '&')
        tokens = split_with_delimiter(tokens, r'{', '{')
        
        tokens = split_with_delimiter(tokens, r'}', '}')
        tokens = [ new_item for substring in tokens for new_item in substring.split('\n') ]

        tokens = list(filter(lambda x: not re.search(r'^ *$', x), tokens))

        return tokens


    def _group_brackets(self, content):
        
        tokens = self._tokenizer(content)

        nest_stack:List[BracketToken] = []
        grouped:List[BracketToken|str] = []
        
        for item in tokens:
            match item:
                case '{'|'&':
                    new_bracket = BracketToken([], '', 'bracket' if item == '{' else 'argument')

                    if len(nest_stack) > 0:
                        nest_stack[-1].content.append(new_bracket)

                    nest_stack.append(new_bracket)
                case '}':
                    if len(nest_stack) == 0:
                        raise SyntaxError(message='Mismatched bracket', file=self.file, lineno=self._find_line(item),content=content)
                    bracket = nest_stack.pop()
                    if len(nest_stack) == 0:
                        grouped.append(bracket)

                case _:
                    if len(nest_stack) == 0:
                        grouped.append(item)
                    else:
                        nest_stack[-1].content.append(item)


        if len(nest_stack) > 0:
            raise SyntaxError(message='Mismatched bracket', file=self.file, lineno=self._find_line('a'),content=content)

        
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

        single_closed_brackets_regex = re.compile(r'^\s+}\n', flags=re.MULTILINE)

        content = re.sub(single_closed_brackets_regex, '}\n', content)

        closed_brackets_without_space_regex = re.compile(r'}\n', flags=re.MULTILINE)
        content = re.sub(closed_brackets_without_space_regex, '} \n', content)

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

        def convert_types(yaml_dict):
            for key in yaml_dict:
                if yaml_dict[key] in ['True', 'true']:
                    yaml_dict[key] = True
                elif yaml_dict[key] in ['False', 'false']:
                    yaml_dict[key] = False
                elif str(yaml_dict[key]).isdigit():
                    yaml_dict[key] = int(yaml_dict[key])

            return yaml_dict

        self.metadata = convert_types(yaml.load(metadata, yaml.BaseLoader))
        
        return re.sub(metadata_regex, '', content)

    def add_block(self, block: Block):
        block.root = self.root
        block.metadata = self.metadata

        self.blocks.append(block)

    def pretty_print(self):
        for block in self.blocks:
            rprint(block.__str__())

    def run_blocks(self):
        is_simulating = False

        rprint(Panel.fit(f'[green underline]Running[blue not underline] "{os.path.basename(self.file)}"[green] in [blue]"{self.root}"', border_style='green'))
        cwd = os.getcwd()

        for block in self.blocks:

            if 'simulate' in block.metadata:
                if block.metadata['simulate'] and not is_simulating:
                    rprint(Rule('[yellow]:warning: Simulating :warning:', style='yellow'))

                is_simulating = block.metadata['simulate']


            rprint(f'[green underline]evaluating[blue not underline] {block.name}')
            pipe = block.eval()
            if not pipe.items:
                rprint(f'    [grey50]nothing to do')
            print('')

            if 'simulate' in block.metadata:
                if block.metadata['simulate'] and not is_simulating:
                    rprint(Rule('[yellow]:warning: Simulation end :warning:', style='yellow'))

        if is_simulating:
            rprint(Rule('[yellow]:warning: Simulation end :warning:', style='yellow'))

        os.chdir(cwd)




if __name__ == '__main__':
    document = Document('./scripts/first.movy')
    document.pretty_print()
    print('-------------')
    document.run_blocks()
