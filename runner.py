# from movy.__main__ import main
from movy.parsing import Document

if __name__ == "__main__":
    document = Document('./movy/scripts/first.movy')
    document.pretty_print()
    print('-------------')
    document.run_blocks()

    # main()
