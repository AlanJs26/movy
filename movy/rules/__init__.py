from .basename import Basename
from .pdf_template import PDF_Template
from .extension import Extension
from .path import Path
from .file import File

RULES = {
    'basename': Basename,
    'extension': Extension,
    'path': Path,
    'file': File,
    'pdf_template': PDF_Template
}
