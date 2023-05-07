from ..classes import Destination_rule, Pipe, Expression, Argument, Regex, PipeItem
from ..classes.exceptions import ActionException
from rich import print as rprint
from ..utils import LetterPrompt
import os
import shutil
from os import path

class Move(Destination_rule):
    def __init__(self, name: str, content: list[str|Expression], arguments: list[Argument], operator: list[str], ignore_all_exceptions=False):
        super().__init__(name, content, arguments, operator, ignore_all_exceptions)

    def _overwrite(self, content_path, item: PipeItem):
        if not self.simulate:
            shutil.move(item.filepath, path.join(content_path, path.basename(item.filepath)))
        item.deleted = True

        rprint(f'[yellow not bold]Overwrite: [green]{path.basename(item.filepath)} [blue]-> {path.split(content_path)[0]+"/" if path.split(content_path)[0] else ""}[bold]{path.split(content_path)[1]}')

    def _rename(self, content_path, item: PipeItem):
        count = 1

        def make_name(oldpath:str):
            nonlocal count
            basename, extension = path.splitext(oldpath)
            new_name = f"{basename}({count}){extension}"
            return new_name

        if new_name := self._eval_argument('new_name', item):
            if isinstance(new_name, Regex):
                raise ActionException(self.name, 'cannot use Regex as argument')
            new_name = new_name.replace('%d', str(count))
        else:
            new_name = make_name(path.basename(item.filepath))


        while path.isfile(path.join(content_path, new_name)):
            new_name = make_name(new_name)
            count+=1

        if not self.simulate:
            shutil.move(item.filepath, path.join(content_path, new_name))
        item.deleted = True

        rprint(f'[yellow not bold]Rename: [green]{path.basename(item.filepath)} [blue]-> {path.split(content_path)[0]+"/" if path.split(content_path)[0] else ""}[bold]{new_name}')

    def eval_item(self, item: PipeItem, pipe: Pipe):
        content = self._eval_content(item)

        if isinstance(content, Regex):
            raise ActionException(self.name, 'cannot use Regex as argument')
        if not self.content:
            raise ActionException(self.name, 'destination path is empty')
        if not content:
            return


        if not path.isdir(content):
            if self._eval_argument('makedirs', item) == 'true':
                if not self.simulate:
                    os.makedirs(content)
            else:
                raise ActionException(self.name, f'directory {content} does not exist. Use the argument "makedirs" to automatically create missing directories')

        if path.isfile(item.filepath):

            if path.isfile(path.join(content, path.basename(item.filepath))):
                rprint(f'[yellow]Move: "{item.filepath}" already exists in destination folder')
                available_choices = ['rename', 'overwrite', 'skip']

                argument_choice = self._eval_argument('on_conflict', item) 

                if argument_choice in available_choices:
                    choice = argument_choice
                else:
                    choice = LetterPrompt.ask('what to do?', choices=available_choices, default='skip')

                if choice == 'overwrite':
                    self._overwrite(content, item)
                elif choice == 'rename':
                    self._rename(content, item)
                elif choice == 'skip':
                    rprint(f'[yellow]ignoring "{path.basename(item.filepath)}"')
            else:
                try:
                    if not self.simulate:
                        shutil.move(item.filepath, content)
                    if self._eval_argument('silent', item) != 'true':
                        rprint(f'[yellow not bold]Move: [green]{path.basename(item.filepath)} [blue]-> {path.split(content)[0]+"/" if path.split(content)[0] else ""}[bold]{path.split(content)[1]}')
                    item.deleted = True
                except shutil.Error:
                    raise ActionException(self.name, f'Unexpected Error while moving {item.filepath}')



        else:
            raise ActionException(self.name, 'this action can only move files')



