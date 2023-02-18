from time import sleep
import os
from rich import print
from argparse import RawTextHelpFormatter, ArgumentParser
from .parsing import Document

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


def string_parse(string):
    if string:
        new_string = dir_path(string, True)
        if new_string:
            return new_string
    print('please provide a valid path to proceed')
    return None

parser = ArgumentParser(description='Move, copy and rename files programmatically', formatter_class=RawTextHelpFormatter)

parser.add_argument('script_path',     action='store', default=[],         type=string_parse, nargs='+',
                    help='path to the script (accepts more than one script at same time)')
parser.add_argument('-d','--daemon',   action='store_true',
                    help='runs the program as a daemon')
parser.add_argument('-s','--simulate',   action='store_true',
                    help='display only. Do not move, delete or copy files')
parser.add_argument('-u','--undo',   action='store_true',
                    help='undo last change')
parser.add_argument('--interval',    action='store', default=60,    type=int,
                    help='interval used at the daemon update (seconds)')
# parser.add_argument('--history',    action='store', default=os.path.join(os.getcwd(), 'history.txt'),    type=lambda x: dir_path(x,True),
#                     help='path to the history file')
parser.add_argument('-r', '--root',    action='store', default='./',    type=dir_path,
                    help='folder to be used as root')

args = parser.parse_args()

# file_history = FileHistory()
# with open(args.history,'r', encoding='utf-8') as f:
#     lines = f.readlines()
#     file_history.history_array = file_history.parse(''.join(lines))

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
# DONE -> add windows support
#     DONE -> launch script by a executable file (in the same way as autohot key
#             create a separate program that converts a movy script into an executable)
#     DONE -> system tray
# TODO -> add load file as parameter in any command, allowing to pick data from csv files
#     TODO -> add way to write these data directly in the script file 
# TODO -> add an "output" action that pipes all matches to the next block
# TODO -> add machine learning document classification
# TODO -> add document tags output / new name for file suggestion
# TODO -> create more ways for handling name conflicts
# TODO -> add file duplicate detection
# TODO -> match folders
# TODO -> add "run external command" action
# TODO -> write README

def main():
    # if args.undo:
    #     move_pairs(file_history.previous_items(), history=file_history) 
    #
    #     with open(args.history,'w', encoding='utf-8') as f:
    #         f.write(file_history.toString().encode('cp850', 'replace').decode('cp850'))
    #     exit()

    if len(args.script_path) == 0:
        print("please provide a script file")
        exit()

    documents: list[Document] = [Document(script) for script in args.script_path]

    if args.daemon:
        print(f'Running as daemon (updating after {args.interval} seconds)')
        try:
            while True:
                print('\nUpdating...')
                for document in documents:
                    document.run_blocks()
                sleep(args.interval)
        except:
            print('\nexiting...')
    else:
        for document in documents:
            document.run_blocks()
