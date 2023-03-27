from ..classes import Input_rule, Regex, Expression, PipeItem, Argument, Property
from ..utils import RuleException

class HasProperty(Input_rule):
    def __init__(self, name: str, operator:str, content: list[str|Expression], arguments: list[Argument], flags: list[str]):
        super().__init__(name,operator,content,arguments,flags)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = self._eval_content(pipe_item)

        supported_properties = ['islink', 'isfile', 'isdir']

        if not content:
            raise RuleException(self.name, 'content field is empty')

        if isinstance(content, Regex):
            raise RuleException(self.name, 'this does not accept regexp as content')
        if content not in supported_properties:
            raise RuleException(self.name, 'unknown property')

        properties = Property(pipe_item.filepath)

        if content == 'islink':
            return properties.islink
        elif content == 'isfile':
            return properties.isfile
        elif content == 'isdir':
            return properties.isdir

        return False



