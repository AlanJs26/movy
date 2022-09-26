import yaml
import os
from PIL import Image
import subprocess
from pystray import MenuItem, Icon, Menu

try:
    with open('settings.yaml') as f:
        settings = {"daemon": True, **yaml.load(f, Loader=yaml.loader.SafeLoader)}
except Exception as e:
    print("cannot read settings.yaml")
    exit()

def addQuotes(text):
    return '"'+text.replace("\\", "/")+'"'

def addRoot(root, scripts):
    return list(map(lambda x: addQuotes(os.path.join(root,x)), scripts))

cwd = os.getcwd()

if not os.path.isdir(cwd+"/scripts/"):
    os.makedirs(cwd+"/scripts/", exist_ok=True)


def run_on_terminal(command):
    prefix = "start cmd /c "
    sufix = " &&pause&&exit"
    full_command = prefix + addQuotes(command+sufix)
    os.system(full_command)
        
command_args = [
    "python",
    addQuotes(os.path.join(cwd, "main.py")),
    *addRoot(cwd+"/scripts/", os.listdir("scripts"))] 

should_open_terminal = False
log_path = "movy_log.txt"

for key in settings:
    if key == 'terminal' and settings[key] == True:
        should_open_terminal = True
        continue
    if key == 'log_path' and settings[key] is str:
        log_path = settings[key]
        continue

    if settings[key] == False:
        continue

    command_args.append("--"+key)
    if not isinstance(settings[key], bool):
        command_args.append(settings[key])

if should_open_terminal:
    run_on_terminal(" ".join(command_args))
else:
    logfile = open(log_path, 'w')
    subprocess.Popen(" ".join(command_args), shell=True, stdout=logfile, stderr=logfile)


    image = Image.open("icon.png")
    menu = Menu(
        MenuItem('Test scripts in terminal', lambda _: run_on_terminal(" ".join(command_args)) ),
        MenuItem('Undo last change', lambda _: run_on_terminal(" ".join(command_args+["--undo"])) ),
        MenuItem('Open scripts...', lambda _:os.system('start /d '+addQuotes(cwd)+" scripts") ),
        MenuItem('Exit', lambda _:icon.stop())
    )
    icon = Icon('name', icon=image, title="Movy folder organizer", menu=menu)
    icon.run()
    