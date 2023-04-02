from ..classes import Input_rule, Regex, Expression, PipeItem, Argument
from fnmatch import fnmatch
from ..utils import extension
from ..classes.exceptions import RuleException

class Extension(Input_rule):
    def __init__(self, name: str, operator:str, content: list[str|Expression], arguments: list[Argument], flags: list[str], ignore_all_exceptions=False):
        super().__init__(name,operator,content,arguments,flags, ignore_all_exceptions)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = self._eval_content(pipe_item)
        path_extension = extension(pipe_item.filepath)

        if not content:
            raise RuleException(self.name, 'content field is empty')

        if isinstance(content, Regex):
            if content.search(path_extension):
                return True
        else:
            if self._eval_argument('strict', pipe_item) == 'true':
                raw_content = self._eval_raw_content(pipe_item)
                if not isinstance(content, Regex):
                    return raw_content in path_extension.split(',')
            else:
                for ext in content.split(','):
                    if fnmatch(path_extension, ext.strip()):
                        return True

        return False


