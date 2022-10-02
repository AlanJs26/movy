import re

def check_ext(text: str, extension: str) -> bool:
    return bool(re.search('.+\\.'+extension+'$', text, flags=re.IGNORECASE))

def get_file_content(file:str, max_lines=10, max_line_length=200) -> str:
    if check_ext(file, 'pdf'):
        import fitz

        try:
            # Open the document
            pdfIn = fitz.open(file)
        except Exception as e:
            return ''

        if pdfIn.pageCount <= 0:
            return ""

        count = 0
        file_content = ""
        for page in pdfIn:
            count += 1
            file_content += page.getText()
            if count >= max_lines:
                break
        
        return file_content
    

    try:
        with open(file,'r') as f:
            lines = ''
            current_line = 0
            while current_line < max_lines:
                current_line+=1
                lines += f.readline(max_line_length)
            return lines
    except:
        return ""

def freeze(d):
    if isinstance(d, dict):
        return frozenset((key, freeze(value)) for key, value in d.items())
    elif isinstance(d, list):
        return tuple(freeze(value) for value in d)
    return d

def mergedicts(dict1, dict2):
    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield (k, dict(mergedicts(dict1[k], dict2[k])))
            else:
                # If one of the values is not a dict, you can't continue merging it.
                # Value from second dict overrides one in first and we move on.
                yield (k, dict2[k])
                # Alternatively, replace this with exception raiser to alert you of value conflicts
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])
