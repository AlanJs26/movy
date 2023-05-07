from ..classes import Input_rule, Regex, Expression, PipeItem, Argument
from os.path import join
from ..utils import extension, tmp_folder
from ..classes.exceptions import RuleException
from rich import print as rprint

def pdf2img(input_file: str, output_name: str) -> str:
    """Converts pdf to image and generates a file by page"""

    if extension(input_file) != 'pdf':
        return ""

    import fitz

    # Open the document
    pdfIn = fitz.open(input_file) # type: ignore

    if pdfIn.page_count <= 0:
        return ""

    page = pdfIn[0] # first page

    pix = page.get_pixmap(alpha=False)
    pix.save(join(tmp_folder, output_name))
    
    pdfIn.close()

    return join(tmp_folder, output_name)

def pdf_similarity(first_pdf:str, second_pdf:str) -> int:
    """Return a score based in the visual similarity between two pdfs"""
    from skimage.metrics import structural_similarity
    from skimage.io import imread
    from skimage.transform import resize
    from skimage.color import rgb2gray

    if extension(first_pdf) ==  'pdf':
        first = imread(pdf2img(first_pdf, 'first.png'))
    else:
        first = imread(first_pdf)

    if extension(second_pdf) ==  'pdf':
        second = imread(pdf2img(second_pdf, 'second.png'))
    else:
        second = imread(second_pdf)

    # shape to the same size
    second = resize(second, first.shape)
    # second = downscale_local_mean(second, first.shape)

    # Convert images to grayscale
    first_gray = rgb2gray(first)
    second_gray = rgb2gray(second)

    # Compute SSIM between two images
    score, _ = structural_similarity(first_gray, second_gray, full=True)

    return score


class PDF_Template(Input_rule):

    def __init__(self, name: str, operator:list[str], content: list[str|Expression], arguments: list[Argument], flags: list[str], ignore_all_exceptions=False):

        self.base_file_png = ''
        super().__init__(name,operator,content,arguments,flags, ignore_all_exceptions)

    def filter_callback(self, pipe_item: PipeItem) -> bool:

        if self.content:
            raise RuleException(self.name, 'this rule only accepts arguments as input')
        if extension(pipe_item.filepath) != 'pdf':
            raise RuleException(self.name, 'this rule only support pdf files')

        base_file = self._eval_argument('base_file', pipe_item)

        if not base_file:
            raise RuleException(self.name, 'base_file argument not found')
        elif isinstance(base_file, Regex):
            raise RuleException(self.name, 'base_file does not accept regexp')
        elif extension(base_file) != 'pdf':
            raise RuleException(self.name, 'base_file should be a pdf file')

        if not self.base_file_png:
            self.base_file_png = pdf2img(base_file, 'first.png')

        second = pdf2img(pipe_item.filepath, 'second.png')
        target_score = self._eval_argument('score', pipe_item)

        if not isinstance(target_score, str):
            raise RuleException(self.name, 'score must be a number')
        if not target_score.isdecimal():
            raise RuleException(self.name, 'score must be a number')

        score = pdf_similarity(self.base_file_png, second)*100

        if self._eval_argument('verbose', pipe_item) == 'true':
            rprint('[yellow]pdf_template')
            rprint(f'[blue]file:[green] {pipe_item.filepath}')
            rprint(f'[blue]base_file:[green] {base_file}')
            if score >= int(target_score):
                rprint(f'[blue]score: [green]{score} >= {target_score}')
            else:
                rprint(f'[blue]score: [red]{score} >= {target_score}')
            rprint('-----')
        return score >= int(target_score)

        





