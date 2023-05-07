from movy.__main__ import main
from movy.parsing import Document
from rich import print as rprint
from rich.console import Console

from movy.utils import LetterPrompt
from movy.classes.content import Property

if __name__ == "__main__":

    # prop = Property('/home/alan/Downloads/comprovante.pdf', {'a': 'jose'})
    # rprint(prop.isfile)


    # print(LetterPrompt.ask("alan", choices=['jose', 'santos']))

    # console = Console()
    #
    # document = Document('./movy/scripts/first.movy')
    #
    # console.rule('Debug')
    #
    # document.pretty_print()
    #
    # console.rule('Running')
    #
    # document.run_blocks()
    #
    # # console.rule('History')
    # #
    # # for block in document.blocks: 
    # #     rprint(repr(block.history))

    main()
