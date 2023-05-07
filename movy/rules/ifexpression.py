from ..classes import Input_rule, Regex, Expression, PipeItem, Argument, Property
from ..classes.exceptions import RuleException
from rich import print as rprint


class IfExpression(Input_rule):
    def __init__(self, name: str, operator:list[str], content: list[str|Expression], arguments: list[Argument], flags: list[str], ignore_all_exceptions=False):
        super().__init__(name,operator,content,arguments,flags, ignore_all_exceptions)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = self._content_to_str()

        expression = Expression(content, ignore_exceptions=False).eval(pipe_item)

        return bool(expression)




