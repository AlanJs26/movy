import re

def check_ext(text: str, extension: str) -> bool:
    return bool(re.search('.+\\.'+extension+'$', text))

def get_file_content(file:str):
    if check_ext(file, 'pdf'):
        import fitz

        # Open the document
        pdfIn = fitz.open(file)

        if pdfIn.pageCount <= 0:
            return ""

        file_content = ""
        for page in pdfIn:
            file_content += page.getText()
        
        return file_content
    

    try:
        with open(file,'r') as f:
            return f.read()
    except:
        return ""


