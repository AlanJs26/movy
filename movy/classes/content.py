import re
from ..classes.exceptions import ExpressionException
from rich import print as rprint
from .pipe import PipeItem
from ..utils import extension

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



class Property():
    def __init__(self, filepath:str):
        self.filepath = filepath

    @property
    def islink(self):
        from os.path import islink
        return islink(self.filepath)
    @property
    def isfile(self):
        from os.path import isfile
        return isfile(self.filepath)
    @property
    def isdir(self):
        from os.path import isdir
        return isdir(self.filepath)

class Expression():
    def __init__(self, content:str, ignore_exceptions = False):
        self.content:str = content
        self.ignore_exceptions = ignore_exceptions

    def eval(self, item: PipeItem):
        import os.path

        try:
            result = eval(self.content, {
                **item.data,
                'os.path': os.path,
                'upper': lambda x:x.upper(),
                'basename': os.path.basename(os.path.splitext(item.filepath)[0]),
                'filename': os.path.basename(item.filepath),
                'extension': extension(item.filepath),
                'property': Property(item.filepath)
            })
        except NameError as e:
            if self.ignore_exceptions:
                return ''
            else:
                raise ExpressionException(self.content, f'Invalid argument {e.name}')

        return result
    
    @staticmethod
    def eval_list(content: 'list[str|Expression]|None', pipe_item: PipeItem) -> str|Regex:
        if not content:
            return ''

        output = ''
        for item in content:
            if isinstance(item, str):
                output += item
                continue

            try:
                output += str(item.eval(pipe_item))
            except ExpressionException as e:
                rprint(str(e))
                return ''
        
        if Regex.is_valid(output):
            return Regex.parse(output)

        return Expression._escape_characters(output)

    @staticmethod
    def _escape_characters(text: str) -> str:
        return text.replace(r'\/', '/').replace('\\}', '}').replace('\\{', '{')

    def __repr__(self):
        return f'Expression({self.content})'


class Argument():
    def __init__(self, name:str, content:list[str|Expression]):
        self.name = name

        self.content = [(item.lstrip() if isinstance(item,str) else item) for item in content]
        self.raw_content = content

    def __repr__(self):
        return f"Argument(name: '{self.name}', content: {self.content})"










