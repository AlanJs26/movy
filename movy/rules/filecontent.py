from ..classes import Input_rule, Regex, Expression, PipeItem, Argument
from ..utils import extension, RuleException
from rich import print as rprint


def get_file_content(file:str, max_lines=10, max_line_length=200) -> str:
    file_content = ''
    try:
        if extension(file) == 'pdf':
            import fitz

            # Open the document
            pdfIn = fitz.open(file) #type: ignore

            current_line = 0
            for page in pdfIn:
                current_line += 1
                file_content += page.get_text()
                if current_line >= max_lines:
                    break
            pdfIn.close()
        else:
            with open(file,'r', encoding='utf-8') as f:
                current_line = 0
                while current_line < max_lines:
                    current_line+=1
                    file_content += f.readline(max_line_length)
    except:
        raise RuleException('filecontent', f'cannot fetch file contents of "{file}"')

    return file_content

class FileContent(Input_rule):
    def __init__(self, name: str, operator:str, content: list[str|Expression], arguments: list[Argument], flags: list[str]):
        super().__init__(name,operator,content,arguments,flags)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = self._eval_content(pipe_item)

        if not content:
            raise RuleException(self.name, 'content field is empty')
        elif not isinstance(content, Regex):
            raise RuleException(self.name, 'content must be a regexp')

        file_content = get_file_content(pipe_item.filepath)

        match = content.search(file_content)

        if self._eval_argument('silent', pipe_item) != 'true':
            rprint(f'[yellow]Filecontent: [cyan]{content.content}  [{"green" if match else "red"}]{pipe_item.filepath}')

        if self._eval_argument('verbose', pipe_item) == 'true':
            print(file_content)

        if not match:
            return False

        pipe_item.data = {
            **pipe_item.data,
            **match.groupdict()
        }

        return True

