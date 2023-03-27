import os
from rich import print as rprint
import re
from typing import Optional, Tuple

tmp_folder = '/tmp'

def extension(text: str) -> str:
    return os.path.basename(os.path.splitext(text)[1]).casefold().strip().replace('.', '')

class RuleException(Exception):
    def __init__(self, action_name: str, message:str):
        self.action_name = action_name
        self.message = message

    def __str__(self):
        output = f'[red]{self.action_name}: {self.message}'

        return output

class ActionException(Exception):
    def __init__(self, action_name: str, message:str):
        self.action_name = action_name
        self.message = message

    def __str__(self):
        output = f'[red]{self.action_name}: {self.message}'

        return output

def parse_action(text:str, action_type:str, pattern_string : Optional[str] = None, flags=re.MULTILINE, rule = None) -> Tuple[str,bool]:
    new_text = ''
    non_text_transformers = ['template']
    not_string_valid = ['filecontent']
    action_results = {}
    options = {}

    
    if action_type == 'regex':
        new_text = text
    elif action_type == 'filename':
        new_text = os.path.basename(text)
    elif action_type == 'entity' and check_ext(text, 'pdf') and rule:
        pattern_string = pattern_string.strip() if pattern_string else None
        options = {
            'maxpages': 2,
            'radius': 20,
            'entities': False,
            'verbose': 'false'
        }

        options = get_rule_options(options, rule)
        content = get_file_content(text, options['maxpages'], 200)

        if pattern_string:
            parsed_pattern_string = re.sub(r'(?<=\|)(\S[^\)\}\]\|\(\[]+?)(?=\||$)', '\\\\b\\1\\\\b', "|"+pattern_string)[1:]
            # parsed_pattern_string = '|'.join("\\b"+item+"\\b" for item in pattern_string.split('|'))
            match_segments = re.findall(f".{{0,{options['radius']}}}"+parsed_pattern_string+f".{{0,{options['radius']}}}", content, flags=flags)
            match_segments = [item.replace('\n', " ") for item in match_segments]
        else:
            match_segments = [content]

        
        if len(match_segments):
            if options['entities']:
                entities = [item.lower().strip() for item in options['entities'].split(',')]
            else:
                entities = [item.lower().strip() for item in pattern_string.split('|')]
            if options['verbose'] == 'true':
                rprint(f"[blue]\\[entity][white] {text}")
                rprint('[green]    segments:')
                for segment in match_segments:
                    print("        "+segment)
                rprint('[green]    entity queries:', end=" ")
                for entity in entities:
                    print(entity, end=", ")
                rprint('\n[green]    found entities:')

            import spacy

            nlp = spacy.load("pt_core_news_sm")

            for segment in match_segments:
                doc = nlp(segment)
                ents = [str(ent).lower() for ent in doc.ents]
                if options['verbose'] == 'true':
                    for e in ents:
                        rprint("[yellow]        "+e, end=", ")
                    print("")
                for entity in entities:
                    if any(re.search(entity, ent, flags=re.I) for ent in ents):
                        return '', True, action_results
        
        return '', False, action_results
            

    elif action_type == 'filecontent':
        valid_extensions = ['pdf', 'txt', 'csv', 'c', 'cpp', 'dat', 'log', 'xml', 'js', 'jsx', 'py', 'html', 'sh']
        if os.path.splitext(text)[-1].replace('.', '') in valid_extensions:
            options = {
                'maxlines': 10,
                'linelength': 200,
                'verbose': 'false'
            }

            options = get_rule_options(options, rule)

            new_text = get_file_content(text, options['maxlines'], options['linelength'])

    if new_text:
        return new_text, True, action_results

    return text, False, action_results
