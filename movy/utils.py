import os
from rich.prompt import PromptBase, InvalidResponse

tmp_folder = '/tmp'

def extension(text: str) -> str:
    return os.path.basename(os.path.splitext(text)[1]).casefold().strip().replace('.', '')

def parse_int(text) -> int|None:
    if isinstance(text, str) and text.isdecimal():
        return int(text)
    return None


class LetterPrompt(PromptBase):
    def check_choice(self, value):
        if not self.choices:
            return False
        letters = list(map(lambda x: x[0], self.choices))
        return value[0] in letters
    
    def make_prompt(self, _):
        if not self.choices:
            return self.prompt+': '
        choices = ','.join(map(lambda x: f'({x[0]}){x[1:]}', self.choices))
        return f'{self.prompt} [magenta][{choices}]: '

    def process_response(self, value):
        if not self.choices:
            return super().process_response(value)
        letters = list(map(lambda x: x[0], self.choices))
        try:
            index = letters.index(value[0])
            return self.choices[index]
        except:
            raise InvalidResponse('[red]Please select one of the available options')


