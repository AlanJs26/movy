from ..classes import Destination_rule, Pipe, Expression, Argument, Regex, PipeItem
from ..classes.exceptions import ActionException

class Set_Defaults(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        super().__init__(name, content, arguments, operator, ignore_all_exceptions)

    def eval_item(self, item: PipeItem, pipe: Pipe):
        content = self._eval_content(item)

        if isinstance(content, Regex):
            raise ActionException(self.name, 'cannot use Regex as argument')
        if not self.content or not content:
            raise ActionException(self.name, 'You must specify an command name')


        for command in pipe.commands:
            if command.name != content:
                continue

            for argument in self.arguments:
                argument_content = Expression.eval_list(argument.content, item)

                command.arguments_defaults[argument.name] = argument_content
                



