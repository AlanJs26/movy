from parsing import *
# import re
# from datetime import datetime
from rich import print
# from typing import List,Callable

r"""
(?P<regex>[^{\s]\S+)\s*(?P<name>\[\[.+]])\s*(?P<operator>\band\b)?
(?P<action>\[[^\[\]]+\]\s*)?(((?P<regex>[^{\s][^\[\]\s]+\s*))?(?P<name>\[\[.+]]\s*)|(?P<regex2>((?<=])|^)\s*[^{\s\[\]][^\[\]\s]+\s*)|\[.+\]\s*\{\n(.+?\n)})(?P<operator>\band\b)?$
(?P<action>\[[^\[\]]+\]\s*)?(((?P<regex>[^{\s][^\[\]\s]+\s*))?(?P<name>\[\[.+]]\s*)|(?P<regex2>((?<=])|^)\s*[^{\s\[\]][^\[\]\s]+\s*)|\[.+\]\s*\{\n(.+?\n\n*)+\s*})(?P<operator>\band\b)?$
"""

data = """
[[action set]]
in [[named]] and
__pycache__/.*\\.py$ [[named]]
-> destinatio/{basename|named}
alternative/{basename}

/another/*.exe/i [[testname]]
[basename] ^alan 
-> destination/{basename|amed}
"""

history = """
[13:27:51,2022-08-13] path/to/folder/file.txt -> new/destination/file.txt
[13:28:44,2022-08-13] path/to/folder/second.txt -> new/destination/second.txt
[13:28:50,2022-08-13] path/to/folder/third.txt -> new/destination/third.txt
"""

# rule = Input_rule(None, '.+', 'regex', False)        

# print(rule.eval())

file_history = FileHistory()


with open('history.txt','r+') as f:
    lines = f.readlines()
    file_history.history_array = file_history.parse(''.join(lines))
    # for item in file_history.history_array:
        # print(vars(item))

blocks = parse_whole_content(data)
result = blocks[0].eval(file_history)
print(result.toString())


exit()
for block in blocks:
    for child in block.input_set.children:
        print(vars(child))
    print('[blue]'+'-'*40)
    for child in block.destination_set.children:
        print(child.content)

    print('[red]'+'-'*60)
