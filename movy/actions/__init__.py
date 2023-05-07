from .echo import Echo
from .move import Move
from .trash import Trash
from .set_defaults import Set_Defaults
from .terminal import Terminal

# TODO: Build prompt action 

ACTIONS = {
    'echo': Echo,
    'trash': Trash,
    'move': Move,
    'terminal': Terminal,
    'set_defaults': Set_Defaults
}

