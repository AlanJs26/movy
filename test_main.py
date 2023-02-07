
r"""
(?P<regex>[^{\s]\S+)\s*(?P<name>\[\[.+]])\s*(?P<operator>\band\b)?
(?P<action>\[[^\[\]]+\]\s*)?(((?P<regex>[^{\s][^\[\]\s]+\s*))?(?P<name>\[\[.+]]\s*)|(?P<regex2>((?<=])|^)\s*[^{\s\[\]][^\[\]\s]+\s*)|\[.+\]\s*\{\n(.+?\n)})(?P<operator>\band\b)?$
(?P<action>\[[^\[\]]+\]\s*)?(((?P<regex>[^{\s][^\[\]\s]+\s*))?(?P<name>\[\[.+]]\s*)|(?P<regex2>((?<=])|^)\s*[^{\s\[\]][^\[\]\s]+\s*)|\[.+\]\s*\{\n(.+?\n\n*)+\s*})(?P<operator>\band\b)?$
"""

# DONE -> run blocks as time routines 
# DONE -> build the cli
# TODO -> add more actions, such as the file content matching
# TODO -> add history and feature of undo changes

data = """
[[routine 1]]
[18h20m] action set
[15h] block_2

[[action set]]
mo or
__pycache__/.*\\.py$ [[named]]
-> [move]destinatio/{basename|named}
[copy]alternative/{basename}

.*\\.exe -> [copy] executablesfolder/
second/{basename}
"""

if __name__ != "__main__":
    exit()
    
from parsing import *
from rich import print

command_aliases = {
    'move': 'moved',
    'copy': 'copied'
}

file_history = FileHistory()

with open('history.txt','r') as f:
    lines = f.readlines()
    file_history.history_array = file_history.parse(''.join(lines))

def run_block(block : Block, count=1, prefix=''):
    result = block.eval(file_history)
    if block.input_set.name:
        print(f"{prefix}[green]evaluating [blue]{block.input_set.name}")
    else:
        print(f"{prefix}[green]evaluating [blue]block_{count}")

    for item in result:
        print(f'{prefix}[yellow]{command_aliases[item[2]]}[white] {item[0].split("/")[-1]} [yellow]to[white] {item[1]}')
    if len(result) == 0:
        print(f'{prefix}[grey30]no match found')
    print('\n')

count = 1
blocks = parse_whole_content(data, 'C:/Users/alanj/Downloads')
routine_blocks = list(filter(lambda x: x.type == 'routine', blocks))
non_routine_blocks = list(set(blocks).difference(routine_blocks))

if len(routine_blocks):
    for block in routine_blocks:
        print(f"[green]running [blue]{block.input_set.name}")
        blocks_to_run = block.run_routine(non_routine_blocks)

        for inner_block in blocks_to_run:
            run_block(inner_block, prefix='    ')
        if len(blocks_to_run) == 0:
            print('[grey30]no match found')
else:
    for block in blocks:
        run_block(block, count)
        count+=1
    
# print(result.toString())


exit()
for block in blocks:
    print(f"name: {block.input_set.name}")
    print(f"type: {block.type}")
    for child in block.input_set.children:
        print(vars(child))
    print('[blue]'+'-'*40)
    for child in block.destination_set.children:
        print(child.content)

    print('[red]'+'-'*60)
