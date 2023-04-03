from movy.__main__ import main
from movy.parsing import Document
from rich import print as rprint
from rich.console import Console

if __name__ == "__main__":
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
