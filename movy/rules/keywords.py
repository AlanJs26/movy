from ..classes import Input_rule, Regex, Expression, PipeItem, Argument
from ..utils import parse_int
from ..classes.exceptions import RuleException
from .filecontent import get_file_content
import re
from os.path import splitext, basename
from fnmatch import fnmatch


class Keywords(Input_rule):
    def __init__(self, name: str, operator:list[str], content: list[str|Expression], arguments: list[Argument], flags: list[str], ignore_all_exceptions=False):
        super().__init__(name,operator,content,arguments,flags, ignore_all_exceptions)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = self._eval_content(pipe_item)

        if not content:
            raise RuleException(self.name, 'content field is empty')
        elif isinstance(content, Regex):
            raise RuleException(self.name, 'You must enter a comma separated list')

        max_pages = parse_int(self._eval_argument('max_pages', pipe_item)) or 10
        max_lines = parse_int(self._eval_argument('max_lines', pipe_item)) or 10
        linelength = parse_int(self._eval_argument('linelength', pipe_item)) or 10


        file_content = ''

        has_match = False
        for item in content.split(','):
            path_basename = basename(splitext(pipe_item.filepath)[0])

            if self._eval_argument('strict', pipe_item) == 'true':
                raw_content = self._eval_raw_content(pipe_item)
                if raw_content == path_basename: 
                    has_match = True
                    continue
            else:
                if fnmatch(path_basename, content.strip()):
                    has_match = True
                    continue

            if not file_content:
                if 'file_content' in pipe_item.data:
                    file_content = pipe_item.data['file_content']
                else:
                    file_content = get_file_content(pipe_item.filepath, max_lines, linelength, max_pages)
                    pipe_item.data['file_content'] = file_content
                if self._eval_argument('verbose', pipe_item) == 'true':
                    print(file_content)


            match = re.search(item, file_content, flags=re.I)

            if match:
                has_match = True
                pipe_item.data = {
                    **pipe_item.data,
                    **match.groupdict()
                }


        return has_match


