import os
from rich import print as rprint
import re
from typing import Optional, Tuple, Union

def check_ext(text: str, extension: str) -> bool:
    return os.path.splitext(text)[1].lower()[1:] == extension
    # return bool(re.search('.+\\.'+extension+'$', text, flags=re.IGNORECASE))

def get_file_content(file:str, max_lines=10, max_line_length=200) -> str:
    if check_ext(file, 'pdf'):
        import fitz

        try:
            # Open the document
            pdfIn = fitz.open(file)

            if pdfIn.pageCount <= 0:
                return ""

            count = 0
            file_content = ""
            for page in pdfIn:
                count += 1
                file_content += page.getText()
                if count >= max_lines:
                    break
            
            pdfIn.close()
        except Exception as e:
            return ''
        
        
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

def get_rule_options(options:dict, rule):
    if type(rule.action_content) == list:
        for opt_key, action_arg in zip(options.keys(), rule.action_content):
            if type(action_arg) == str and action_arg.isnumeric():
                options[opt_key] = int(action_arg)
            else:
                options[opt_key] = action_arg

    children_dict = rule.get_children_as_dict()
    for key, child_dict in children_dict.items():
        if key in options:
            if type(child_dict['content']) == str and child_dict['content'].isnumeric():
                options[key] = int(child_dict['content'])
            else:
                options[key] = child_dict['content']
    
    return options


def parse_action(text:str, action_type:str, pattern_string : Optional[str] = None, flags=re.MULTILINE, rule = None) -> Tuple[str,bool]:
    new_text = ''
    non_text_transformers = ['template']
    not_string_valid = ['filecontent']
    action_results = {}
    options = {}

    
    if action_type == 'regex':
        new_text = text
    elif action_type == 'extension':
        new_text = os.path.splitext(text)[-1].replace('.', '')
        pattern_string = f"^{pattern_string}$"
    elif action_type == 'filename':
        new_text = os.path.basename(text)
    elif action_type == 'basename':
        new_text = os.path.splitext(os.path.basename(text))[0]
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
    elif action_type == 'template' and check_ext(text, 'pdf') and rule:
        pattern_string = pattern_string.strip() if pattern_string else None
        if not pattern_string or re.search(pattern_string, text, flags=flags):
            from similarity import pdf_similarity

            options = {
                'path': '',
                'threshold': 70,
                'verbose': 'false'
            }

            options = get_rule_options(options, rule)
            
            if check_ext(options['path'], 'pdf'):
                score = pdf_similarity(options['path'], text)

                if options['verbose'] == 'true':
                    rprint(f'[cyan]template[white] -> [blue]path: [white]{options["path"]} [blue]filepath:[white] {text} [{"green" if score*100 > options["threshold"] else "red"}]score: [white]{score*100:.2f}')

                return '', score*100 > int(options['threshold']), action_results

    if pattern_string and action_type not in non_text_transformers:
        try:
            text_match = re.search(pattern_string, new_text, flags = flags)
        except:
            print(pattern_string)
            text_match = None


        matchdict = ()
        matchgroups = ()
        if text_match:
            matchdict = text_match.groupdict()
            matchgroups = text_match.groups()

            if not hasattr(action_results, action_type):
                action_results[action_type] = {}

            if action_type not in not_string_valid:
                action_results[action_type]['string'] = text_match.string
            else:
                action_results[action_type]['string'] = ''
            
            if (len(matchdict) or len(matchgroups)) and not hasattr(action_results, action_type):
                action_results[action_type]['groups'] = {}

            if len(matchdict):
                action_results[action_type]['groups'] = { **action_results[action_type]['groups'], **text_match.groupdict() }
            if len(matchgroups):
                action_results[action_type]['groups'] = { **action_results[action_type]['groups'], **dict(zip(range(1,len(matchgroups)+1), matchgroups)) }
            
        match_result = bool(text_match)

        if action_type == 'filecontent' and 'verbose' in options and options['verbose'] in ['true', 'minimal']:
            rprint(f'[cyan]filecontent [white]-> [blue]filepath: [white]{text} [blue]match: {"[green]true" if match_result else "[red]false"} [blue]pattern: [white]{pattern_string}')
            if options['verbose'] == 'true':
                print(new_text)
            else:
                if len(matchdict): print(matchdict)
                if len(matchgroups): print(matchgroups)

        return '', match_result, action_results

    if new_text:
        return new_text, True, action_results

    return text, False, action_results


def parse_placeholder(destination_item: Tuple[str, Union[str,None]], input_match):
    dest_action,dest_name = destination_item

    if dest_action == 'ignore':
        return ''

    command_match = re.search(r'((?P<command>\w+)\( *)?(?P<content>[\w\.]+)( *\))?', dest_action).groupdict()

    if command_match['content'] is None:
        return None

    new_text = ''
    dest_action_split = command_match['content'].split('.')

    if len(dest_action_split) > 1:
        if dest_action_split[1] == 'groups':
            try:
                if dest_action_split[2].isnumeric():
                    dest_action_split[2] = int(dest_action_split[2])
                new_text = input_match[2][dest_action_split[0]]['groups'][dest_action_split[2]]
            except:
                return None
    elif command_match['content'] in input_match[2]:
        new_text = input_match[2][command_match['content']]['string']

    if new_text:
        if command_match['command'] is not None:
            if command_match['command'] == 'lowercase':
                new_text = new_text.lower()
            elif command_match['command'] == 'uppercase':
                new_text = new_text.upper()
            elif command_match['command'] == 'titlecase':
                new_text = new_text.title()
        
        return new_text

    parsed_action_text, parse_status, _ = parse_action(input_match[0], dest_action)
    if parse_status == False:
        return None

    return parsed_action_text
