from .echo import Echo
from .move import Move
from .trash import Trash
from .set_defaults import Set_Defaults
from .terminal import Terminal
from .prompt import Prompt

# TODO: Build prompt action 

ACTIONS = {
    'echo': Echo,
    'trash': Trash,
    'move': Move,
    'terminal': Terminal,
    'prompt': Prompt,
    'set_defaults': Set_Defaults
}

