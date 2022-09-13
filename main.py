from genericpath import isdir, isfile
from parsing import *
from time import sleep
import yaml
import os
from rich import print
from argparse import RawTextHelpFormatter, ArgumentParser
from typing import Optional
import shutil

command_aliases = {
    'move': 'moved',
    'copy': 'copied',
}

def dir_path(string, asfile=False):
    if string == '': return
    new_string = os.path.expanduser(string)
    if asfile:
        if not os.path.isfile(new_string):
            try:
                os.makedirs(os.path.dirname(new_string), exist_ok=True)
                open(new_string, 'a').close()
            except:
                print(f'[red]"{string}" is not a valid file')
                return
    elif not os.path.isdir(new_string):
            print(f'[red]"{string}" is not a valid directory')
            return

    return new_string


def string_arr(string):
    split_string = string.split()
    output = []
    if string:
        for item in split_string:
            new_string = dir_path(item, True)
            if new_string:
                output.append(new_string)
            else:
                return []
    if len(output) == 0:
        print('please provide a valid path to proceed')
    return output

def move_pairs(files, history : Optional[FileHistory]=None, prefix=''):
    if len(files) == 0:
        if history:
            print("[grey30]nothing to undo")
        else:
            print("[grey30]nothing to do")
        return

    for item in files:
        input_path, dest_path, operation = item

        if os.path.isfile(dest_path) and args.overwrite == False:
            print(f'{prefix}[blue]skiping duplicate... [yellow]{command_aliases[operation]}[white] {input_path.split("/")[-1]} [yellow]to[white] {dest_path}')
        else:
            print(f'{prefix}[yellow]{command_aliases[operation]}[white] {input_path.split("/")[-1]} [yellow]to[white] {dest_path}')

        if args.simulate:
            continue
        if(history):
            history.remove(dest_path, input_path)

        if '.' in os.path.basename(dest_path):
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        else:
            os.makedirs(dest_path, exist_ok=True)

        if args.overwrite:
            dest_path = os.path.join(dest_path, os.path.basename(input_path))

        if operation == 'move':
            try:
                shutil.move(input_path, dest_path)
            except:
                if args.overwrite == False:
                    print(f'{prefix}[red]error moving file')
        elif operation == 'copy':
            try:
                shutil.copy(input_path, dest_path)
            except:
                if args.overwrite == False:
                    print(f'{prefix}[red]error copying file')

parser = ArgumentParser(description='Move, copy and rename files programmatically', formatter_class=RawTextHelpFormatter)

parser.add_argument('script_path',     action='store', default=[],         type=string_arr, nargs='?',
                    help='path to the script (accepts more than one script at same time)')
parser.add_argument('-d','--daemon',   action='store_true',
                    help='runs the program as a daemon')
parser.add_argument('-s','--simulate',   action='store_true',
                    help='display only. Do not move or copy files')
parser.add_argument('-u','--undo',   action='store_true',
                    help='undo last change')
parser.add_argument('--interval',    action='store', default=60,    type=int,
                    help='interval used at the daemon update (seconds)')
parser.add_argument('-f','--force',    action='store_true',
                    help='run all blocks in the script ignoring the configured routines')
parser.add_argument('-w','--overwrite',    action='store_true',
                    help='overwrite files on duplicates. The default behaviour is skip duplicates.')
parser.add_argument('--history',    action='store', default=os.path.join(os.path.expanduser('~'), '.movy/history.txt'),    type=lambda x: dir_path(x,True),
                    help='path to the history file')
parser.add_argument('-r', '--root',    action='store', default='./',    type=dir_path,
                    help='path used as root')

args = parser.parse_args()

file_history = FileHistory()
with open(args.history,'r') as f:
    lines = f.readlines()
    file_history.history_array = file_history.parse(''.join(lines))

# DONE -> run blocks as time routines 
# DONE -> build the cli
# DONE -> fix undo history
# DONE -> implement block filters
# DONE -> add pdf similarity filter
# DONE -> add comments
# DONE -> add vscode,sublime text, vim,... syntax highlighing
# DONE -> add file content filter
# DONE -> add a more robust destination string placeholders
#     DONE -> regex groups
#     DONE -> filter specific string format
# TODO -> add windows support
#     TODO -> launch script by a executable file (in the same way as autohot key
#             create a separate program that converts a movy script into an executable)
#     TODO -> system tray
# TODO -> match folders
# TODO -> add "run external command" action
# TODO -> add aliases
# TODO -> write README

if args.undo:
    move_pairs(file_history.previous_items(), history=file_history) 

    with open(args.history,'w') as f:
        f.write(file_history.toString())
    exit()

if len(args.script_path) == 0:
    exit()

scripts = []
for current_script_path in args.script_path:
    with open(current_script_path,'r') as f:
        scripts.append(f.read())

yaml_regex = re.compile(r'^\s*-{3,}(.+?)-{3,}', re.DOTALL)


blocks = []
for script in scripts:
    new_args = vars(args)

    yaml_match = re.search(yaml_regex, script)
    if yaml_match:
        parsed_yaml = yaml.load(yaml_match.group(1), yaml.BaseLoader)
        for arg_name in vars(args):
            if arg_name in parsed_yaml:
                new_args[arg_name] = parsed_yaml[arg_name]

    blocks.extend(parse_whole_content(script, new_args['root']))
routine_blocks = list(filter(lambda x: x.type == 'routine', blocks))
non_routine_blocks = list(set(blocks).difference(routine_blocks))

            

def run_block(block : Block, prefix=''):
    result = block.eval(file_history)
    with open(args.history,'w', encoding='utf-8') as f:
        f.write(file_history.toString().encode('cp850', 'replace').decode('cp850'))

    if block.input_set.name:
        print(f"{prefix}[green]evaluating [blue]{block.input_set.name}")

    move_pairs(result)

    print('\n')



def run_script():
    global routine_blocks
    global non_routine_blocks

    if len(routine_blocks) and args.force == False:
        for block in routine_blocks:
            print(f"[green]running [blue]{block.input_set.name}")
            blocks_to_run = block.run_routine(non_routine_blocks)

            for inner_block in blocks_to_run:
                run_block(inner_block, prefix='    ')
            if len(blocks_to_run) == 0:
                print('[grey30]no match found')
    else:
        for block in non_routine_blocks:
            run_block(block)


if args.daemon:
    print(f'Running as daemon (updating after {args.interval} seconds)')
    try:
        while True:
            print('\nUpdating...')
            run_script()
            sleep(args.interval)
    except:
        print('\nexiting...')
else:
    run_script()
