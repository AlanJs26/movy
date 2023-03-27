from .basename import Basename
from .pdf_template import PDF_Template
from .extension import Extension
from .path import Path
from .file import File
from .hasproperty import HasProperty
from .filecontent import FileContent

RULES = {
    'basename': Basename,
    'extension': Extension,
    'path': Path,
    'file': File,
    'pdf_template': PDF_Template,
    'hasproperty': HasProperty,
    'filecontent': FileContent,
}



