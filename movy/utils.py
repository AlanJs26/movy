import os

tmp_folder = '/tmp'

def extension(text: str) -> str:
    return os.path.basename(os.path.splitext(text)[1]).casefold().strip().replace('.', '')

