from ..classes import Input_rule, Regex, Expression, PipeItem, Argument
from ..utils import extension, parse_int
from ..classes.exceptions import RuleException
from rich import print as rprint
from unidecode import unidecode


def get_file_content(file:str, max_lines=10, max_line_length=200, max_pages = 10) -> str:
    file_content = ''
    try:
        if extension(file) == 'pdf':
            import fitz

            # Open the document
            pdfIn = fitz.open(file) #type: ignore

            current_page = 0
            for page in pdfIn:
                current_page += 1
                file_content += page.get_text()
                if max_pages > 0 and current_page >= max_pages:
                    break
            pdfIn.close()
        elif extension(file) not in ['appimage', 'zip', 'c', 'deb', 'doc', 'docx', 'gif', 'grfix9', 'gz', 'html', 'iso', 'jpeg', 'jpg', 'mp4', 'png', 'pptx', 'rar', 'srt', 'tgz', 'torrent', 'xlsx', 'xod', 'zip', 'zst']:
            with open(file,'r', encoding='utf-8') as f:
                current_line = 0
                while current_line < max_lines:
                    current_line+=1
                    file_content += f.readline(max_line_length)
    except:
        raise RuleException('filecontent', f'cannot fetch file contents of "{file}"')

    return unidecode(file_content)

class FileContent(Input_rule):
    def __init__(self, name: str, operator:list[str], content: list[str|Expression], arguments: list[Argument], flags: list[str], ignore_all_exceptions=False):
        super().__init__(name,operator,content,arguments,flags, ignore_all_exceptions)

    def filter_callback(self, pipe_item: PipeItem) -> bool:
        content = self._eval_content(pipe_item)

        if not content:
            raise RuleException(self.name, 'content field is empty')
        elif not isinstance(content, Regex):
            raise RuleException(self.name, 'content must be a regexp')

        max_pages = parse_int(self._eval_argument('max_pages', pipe_item)) or 10
        max_lines = parse_int(self._eval_argument('max_lines', pipe_item)) or 10
        linelength = parse_int(self._eval_argument('linelength', pipe_item)) or 10

        if 'file_content' in pipe_item.data:
            file_content = pipe_item.data['file_content']
        else:
            file_content = get_file_content(pipe_item.filepath, max_lines, linelength, max_pages)
            pipe_item.data['file_content'] = file_content

        match = content.search(file_content)

        if self._eval_argument('verbose', pipe_item) == 'true':
            print(file_content)

        if self._eval_argument('minimal', pipe_item) == 'false':
            rprint(f'[yellow]Filecontent: [cyan]{content.content}  [{"green" if match else "red"}]{pipe_item.filepath}')
        elif self._eval_argument('minimal', pipe_item) == 'true' and match:
            rprint(f'[yellow]Filecontent: [cyan]{content.content}  [green]{pipe_item.filepath}')

        if not match:
            return False

        pipe_item.data = {
            **pipe_item.data,
            **match.groupdict()
        }

        return True


