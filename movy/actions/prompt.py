from ..classes import Destination_rule, Pipe, Expression, Argument, PipeItem
from rich import print as rprint
from pick import pick
from rich.prompt import Prompt as Rich_Prompt
from dataclasses import dataclass

@dataclass
class PromptData():
    result:str

    def __str__(self):
        return self.result


class Prompt(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        super().__init__(name, content, arguments, operator, ignore_all_exceptions)

    def eval_all(self, pipe: Pipe):
        self.ensure_not_empty(self.content)

        content = self.ensure_string(self._eval_content(PipeItem('',[])))
        if not content:
            return

        choices = self._eval_argument('choices', PipeItem('',[]))

        if choices and isinstance(choices, str):
            choices = [item.strip() for item in choices.split(',')]

            result, _ = pick(choices, title=content, indicator='->')
            if not isinstance(result, str):
                result = ''
        else:

            default = self._eval_argument('default', PipeItem('',[]))
            if default and isinstance(default, str):
                result = Rich_Prompt.ask(content, default=default)
            else:
                result = Rich_Prompt.ask(content)

        for item in pipe.items:
            item.data['prompt'] = PromptData(result)

    def eval_item(self, item: PipeItem, pipe: Pipe):

        content = self.ensure_string(self._eval_content(item))

        self.ensure_not_empty(self.content)

        if not content:
            return

        choices = self._eval_argument('choices', item)

        if choices and isinstance(choices, str):
            choices = [item.strip() for item in choices.split(',')]

            result, _ = pick(choices, title=content, indicator='->')
            if not isinstance(result, str):
                result = ''
        else:

            default = self._eval_argument('default', item)
            if default and isinstance(default, str):
                result = Rich_Prompt.ask(content, default=default)
            else:
                result = Rich_Prompt.ask(content)

        item.data['prompt'] = PromptData(result)

            



