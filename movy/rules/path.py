from ..classes import Input_rule, Regex, Expression, PipeItem, Argument
from fnmatch import fnmatch

class Path(Input_rule):
    def __init__(self, name: str, operator:str, content: list[str|Expression], arguments: list[Argument], flags: list[str]):
        super().__init__(name,operator,content,arguments,flags)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = Expression.eval_list(self.content, pipe_item)

        if not content:
            raise Exception('basename require content')

        if isinstance(content, Regex):
            if content.search(pipe_item.filepath):
                return True
        else:
            if self._eval_argument('strict', pipe_item) == 'true':
                raw_content = self._eval_raw_content(pipe_item)
                return raw_content == pipe_item.filepath
            else:
                return fnmatch(pipe_item.filepath, content.strip())

        return False



