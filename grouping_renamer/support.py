import os
import re
import logging
from typing import List
from collections import OrderedDict
import typer # temp, should go away with migrate to logging

__author    = "Wayne Stidolph"
__email     = "wayne@stidolph.com"
__license   = "MIT License (see file LICENSE)"
__copyright = "Copyright Wayne Stidolph, 2023"
__status    = "Development"

log = logging.getLogger('support')

verbose_level:int=3
def set_verbosity(level: int):
    verbose_level = level
    logging.basicConfig(level=level)
    
is_dry_run=True
def set_is_dry_run(dryrun):
    global is_dry_run
    is_dry_run=dryrun
    return

def get_is_dry_run():
    global is_dry_run
    return is_dry_run
    
# move to 'id_handling' module?
def get_id_match(filename, id_regex):
    """extract the embedded ID, which is the *last* match to the id_regex"""
    id_matchs=re.findall(id_regex,filename)
    if len(id_matchs) > 0:
        return id_matchs[-1]
    else:
        return None

def get_fullid(filename, idrgx):
    """extract the entire prefix and ID as a single string"""
    rex = '.*'+idrgx
    p = re.compile(rex)
    return  p.match(filename)

def get_next_id(current_id, id_step, id_len) -> str:
    """get the string ID that follows the current ID"""
    newid = current_id+id_step
    return str(newid).rjust(id_len, '0')


def change_dir(path) -> bool:
    """centralize the error reporting for changing dir"""
    try:
        os.chdir(path)
        log.info("change to: {0}".format(os.getcwd()))
        return True
    except FileNotFoundError:
        log.error("Directory: {0} does not exist".format(path))
        return False
    except NotADirectoryError:
        log.error("{0} is not a directory".format(path))
        return False
    except PermissionError:
        log.error("You do not have permissions to change to {0}".format(path))
        return False

def find_case_insensitive(orig_list: list[str], dlist: list[str])-> list[str]:
    """compare case insensitive but return entry from dirlist"""
    return_lines = [] 
    lower_ol = [x.lower() for x in orig_list]
    lower_dl = [x.lower() for x in dlist]
    # match based on lower cased but return from dirlist at that index
    for ol in lower_ol:
        try: 
            return_lines.append(dlist[lower_dl.index(ol)])
        except: # might not be in dirlist at all, in which case forget this entry
            pass 
    return return_lines    

def fetch_ignore(ignore_file_name = 'gfr.ignore') -> list[str]:
    
    """read in the list of directory names to be pruned from os.walk"""
    folder=os.getcwd()
    excluded_dir = loadfile_lines(folder, ignore_file_name)
    return excluded_dir
           
def get_dirs_to_process(startdir: str, exclude: list[str], do_subtree:bool) -> list[str]:
    dirs_to_process = [os.path.abspath(startdir)] # always do startdir
    if do_subtree: # then just add to subdir list 
        for node, dirs, files in os.walk(startdir, topdown=True):
            dirs_to_process = dirs_to_process + [
                os.path.abspath(os.path.join(node, d))
                for d in dirs if d not in exclude]
            dirs[:]=[d for d in dirs if d not in exclude] # assign to dirs to prune
    log.info('processing dirs: ' + str(dirs_to_process))
    return dirs_to_process
      
def fetch_lists(folder, orderfile_name, adapt_case=False) -> list[List[str], List[str]]:
    """Get the contents of the name-ordering file and the directory's actual files list;
    if adapt_case then load the orderfile even if it's under a
    differently-cased name."""
    
    dirlist = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder,f))]
    
    orderedlines_init = []  # Create an empty list to store the candidate filenames  
    # if we have an orderfile, let's read in the lines as the initial value
    have_ofile = os.path.exists(os.path.join(folder, orderfile_name))
    if not have_ofile and adapt_case: # since adapt_case we'll try alternate case
        # try alternate-case versions for the orderfile
        alt_case_matches = find_case_insensitive([orderfile_name], dirlist)
        if alt_case_matches:
            orderfile_name = alt_case_matches[0] # get op sys case'd filename
            have_ofile = True
        
    if have_ofile:
        orderedlines_init = loadfile_lines(folder, orderfile_name)

    else: # never found the order file, so we'll use the
          # sorted-by-name dirlist as the initial ordering value
        log.info('no orderfile ' + orderfile_name + ' in '+ folder)
          
    return [dirlist, orderedlines_init]
  
def loadfile_lines(folder, fname)->list[str]:
    return_lines=[]
    path_to_file=os.path.join(folder, fname)
    if os.path.isfile(path_to_file):
        with open(path_to_file, 'r') as file:
            # Iterate over the lines of the file
            for line in file:
                # Remove the newline character at the end of the line
                line = line.strip()
                return_lines.append(line)
    else:
        log.error('loadfile_lines cannot find '+folder+ ' '+fname)
    return return_lines
def remove_any_matching(tgt: list[str], exclude_patterns: list[str]) -> list[str]:
    """from a list of strings remove all which match any of a list of regexs;
        return new list of non-matched strings"""

    # if nothing to exclude, just send back a copy of input
    if not exclude_patterns:
        return tgt.copy()

    regs = [re.compile(ex) for ex in exclude_patterns]
    
    def match_any(s: str) -> bool:
        for rx in regs:
            if rx.search(s): return True
        return False
    unmatched = [tstr for tstr in tgt if not match_any(tstr)] 
    
    return unmatched
    
def scrub_dups(strlist: list[str])-> list[str]:
    ol_de_duped = list(OrderedDict.fromkeys(strlist))
    if '' in ol_de_duped: ol_de_duped.remove('')
      
    return ol_de_duped   

def scrub_not_matching(strlist: list[str], must_regex: str) -> list[str]:
    if not must_regex or must_regex == '': # just shortcut
        processed_sl = strlist.copy()
    else: # needs checking
        p = re.compile(must_regex)
        processed_sl= [s for s in strlist if p.search(s) ]
    return processed_sl

def find_case_insensitive(orig_list: list[str], dlist: list[str])-> list[str]:
    """compare case insensitive but return entry from dirlist"""
    return_lines = [] 
    lower_ol = [x.lower() for x in orig_list]
    lower_dl = [x.lower() for x in dlist]
    # match based on lower cased but return from dirlist at that index
    for ol in lower_ol:
        try: 
            return_lines.append(dlist[lower_dl.index(ol)])
        except: # might not be in dirlist at all, in which case forget this entry
            pass 
    return return_lines