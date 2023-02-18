from movy.parsing import Document

document = Document('./movy/scripts/first.movy')
document.pretty_print()
print('-------------')
document.run_blocks()
