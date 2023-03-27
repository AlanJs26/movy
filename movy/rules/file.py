from ..classes import Input_rule, Regex, Expression, PipeItem, Argument
from os.path import basename
from fnmatch import fnmatch
from ..utils import RuleException

class File(Input_rule):
    def __init__(self, name: str, operator:str, content: list[str|Expression], arguments: list[Argument], flags: list[str]):
        super().__init__(name,operator,content,arguments,flags)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = Expression.eval_list(self.content, pipe_item)
        path_basename = basename(pipe_item.filepath)

        if not content:
            raise RuleException(self.name, 'content field is empty')

        if isinstance(content, Regex):
            if content.search(path_basename):
                return True
        else:
            if self._eval_argument('strict', pipe_item) == 'true':
                raw_content = self._eval_raw_content(pipe_item)
                return raw_content == path_basename
            else:
                return fnmatch(path_basename, content.strip())

        return False



