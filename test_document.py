from movy.parsing import Document, FileHistory
from os.path import basename

class TestBasename():
    def test_strict(self):
        content = r'''
    ---
    root: ./script_tests
    ---
    [[Basename test]]
    basename:alan {
        strict: true
    }
    '''
        document = Document(text=content)
        pipe = document.blocks[0].eval(FileHistory())

        result = [basename(item.filepath) for item in pipe.items]
        assert result == ['alan.txt']
    def test_basename(self):
        content = '''
    ---
    root: ./script_tests
    ---
    [[Basename test]]
    basename: al*n
    '''
        document = Document(text=content)
        pipe = document.blocks[0].eval(FileHistory())

        result = [basename(item.filepath) for item in pipe.items]
        assert result == ['alan.txt']
