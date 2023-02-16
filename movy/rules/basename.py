from ..classes import Input_rule, Regex, Expression, PipeItem, Argument
from os.path import basename
from fnmatch import fnmatch

class Basename(Input_rule):
    def __init__(self, name: str, operator:str, content: list[str|Expression], arguments: list[Argument], flags: list[str]):
        super().__init__(name,operator,content,arguments,flags)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = Expression.eval_content(self.content, pipe_item)

        if isinstance(content, Regex):
            if content.search(basename(pipe_item.filepath)):
                return True
        else:
            if self._get_argument('strict') == True:
                return content == basename(pipe_item.filepath)
            else:
                return fnmatch(pipe_item.filepath.strip(), content.strip())

        return False



