#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Rename files like <dir>/<prefix><ID><suffix>.<ext>
according to ordering file while retaining grouping.

Usage: see --help

NOTE: partly written to force me into learning some Python (3.11),
so apologies if coding sucks/is non-Pythonic (suggestions for improvement?)
"""

from collections import OrderedDict
import datetime
import logging
import os
from os import path
from os import access, R_OK
from os.path import isfile
import re
from typing import List
from typing_extensions import Annotated

import typer

__author    = "Wayne Stidolph"
__email     = "wayne@stidolph.com"
__license   = "MIT License (see file LICENSE)"
__copyright = "Copyright Wayne Stidolph, 2023"
__status    = "Development"

main=typer.Typer() # for command processing

# LOGGING seems like overfill to instantaite multiple Loggers etc
# just do something pretty simple for now
def notify_user(msg):
    if is_dry_run:
        typer.echo(msg) #get nice color effects or whatnot
    else:    
        logging.info(msg) # might be piped to log file, don't do fancy
        
def notify_user_prob(msg: str):
    if verbose_level > 0:
        notify_user(msg)
def notify_user_dir(msg: str):
    if verbose_level > 1:
        notify_user(msg)
def notify_user_file(msg: str):
    if verbose_level > 2:
        notify_user(msg)

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
        notify_user_prob('loadfile_lines cannot find '+folder+ ' '+fname)
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

def fix_orderlines(orig_ol: list[str],
                   dirlist: list[str],
                   exclude_list: list[str],
                   adapt_to_case:bool,
                   must_regex='') -> list[str]:
    """return new array of files to process, based on the original ordered list
    but with:
    * duplicates and blanks removed
    * case adjusted to match what the OS reports
    * excluding names that start with any entry entry in exclude_list,
    * exluding names that don't match the (option) must_regex (blank or * 
    regex matches all string after the exclud_list is applied)
    """
    
    ol_de_duped= scrub_dups(orig_ol)
    ol_excluded = remove_any_matching(ol_de_duped, exclude_list) 
    processed_ol = scrub_not_matching(ol_excluded, must_regex)

    # now, anything in the processed orderlist might be of interest
    # (if, and only if, we find it in the list of filenames ('dirlist'))
    if adapt_to_case :
        final_lines = find_case_insensitive(processed_ol, dirlist)
    else:
        final_lines = [line for line in processed_ol if line in dirlist]
    return final_lines

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
        notify_user_dir('no orderfile ' + orderfile_name + ' in '+ folder)
          
    return [dirlist, orderedlines_init]

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

def make_rename_list(orderednames: list[str], idregex: str, to_pref:str, id_prefix:str,
                     idstart: int, idstep:int, idlen:int=4):
    """build replacement list, new names given by
       to_pref + id_prefix + calculated ID + end of existing name"""
    # treat orderfile specially
    repl_list=[]
    current_id:str = get_next_id(idstart-idstep,idstep, idlen)
    used_current_id=False
    used_id_counter = 0
    on_len = len(orderednames)
    
    for on_idx in range(0, on_len):
        name_to_update = orderednames[on_idx]
        
        if name_to_update: # might be '', a previously a deleted entry
            fullid = get_fullid(name_to_update, idregex) # e.g., 'a_100'

            if fullid:
            # note if it doesn't have an embedded IF ID then
            # fullid won't match and file will not be renamed 
               
                newstart=to_pref + id_prefix + current_id
                for x in range(on_idx, on_len):
                # for this and every remaining entry in ordered names
                    origname=orderednames[x]

                    if origname.startswith(fullid.group()):
                        # if we find another that matches the fullid
                        # build a 'to' which is the target group and next ID
                        # then we add to rename list
                        repl_list.append({
                            'from': origname,
                            'to': newstart+origname[fullid.span()[1]:]
                        })
                        used_current_id=True
                        orderednames[x]='' # and delete the entry from 'orderednames'
        if used_current_id:
            used_id_counter += 1
            current_id=get_next_id(int(current_id), idstep, idlen)
            used_current_id=False
    return repl_list
    
def do_rename(rename_list, hist_file_obj) -> List[str]:
    """execute the rename_list (of objects with 'from' and 'to' filenames) """
    used_newnames=[] # array of used to-names
    for rename_item in rename_list:
        fname = rename_item['from']
        tname = rename_item['to']
        
        is_sane = True
        if os.path.isfile(tname):
            notify_user_prob('"to" file already exists: ' + tname)
            is_sane=False
        if not os.path.exists(fname):
            notify_user_prob('"from" file missing: ' + fname)
            is_sane= False
        if is_sane :
            if verbose_level > 1: 
                notify_user_file('renaming: '+ fname + ' to '+ tname)
            used_newnames.append(tname)
            if not is_dry_run:
                os.rename(fname, tname)
                hist_file_obj.write(fname+','+tname+'\n')
    
    notify_user_dir('dir '+os.getcwd()+' renamed '+ str(len(used_newnames)) + ' files')
    return used_newnames

def change_dir(path) -> bool:
    """centralize the error reporting for changing dir"""
    try:
        os.chdir(path)
        notify_user_dir("change to: {0}".format(os.getcwd()))
        return True
    except FileNotFoundError:
        notify_user_prob("Directory: {0} does not exist".format(path))
        return False
    except NotADirectoryError:
        notify_user_prob("{0} is not a directory".format(path))
        return False
    except PermissionError:
        notify_user_prob("You do not have permissions to change to {0}".format(path))
        return False
    
def make_bu_name(fn: str, bustr: str):
    """add backup-indication string (bustr) to the fn without change file extension"""
    ld=fn.rfind('.')
    if(ld <0): # no dot at all
        return fn+'__'+bustr
    else:
        return fn[:ld]+'__'+bustr+fn[ld:]
    
def rename_in_dir(path, prefix_ctl,
                 orderfile_name, history_file,
                 id_prefix, id_regex, idstart, idstep, idlen,
                 skip_if_no_orderfile,
                 adapt_case=True) -> list[str]:
    """execute renaming in a single folder"""
    notify_user('do_in_folder ' + path)
    if not change_dir(path): # TODO change to pass path, not changing directory
       return []

    is_orderfile = isfile(orderfile_name)
    if (not is_orderfile or not access(orderfile_name, R_OK)) and skip_if_no_orderfile:
        notify_user_dir('skipping '+path+ ' because no readable orderfile '+orderfile_name)
        notify_user_dir('is_orderfile is'+ str(is_orderfile))
        return []
    
    (dirlist, orderedlines_init) = fetch_lists('.', orderfile_name)
    if not orderedlines_init: orderedlines_init = sorted(dirlist) # TODO other sort flags?
    
    exclude_from_renaming = [orderfile_name, r'rename_history.*','.gitignore'] # TODO make a param?  
    # WORKING HERE ON THE rename/undo/rename sequnce generating date-appended fssort__...  
        
    orderedlines=fix_orderlines(orderedlines_init,
                dirlist, exclude_from_renaming, adapt_case, id_regex)
    # orderedlines holds list of files which exist in dir, with no duplicates,
    # are not in the exclude_from_renaming list, and meet the must_regex 

    if len(orderedlines) == 0:  # nothing to rename, no need to do a history file
        return [] # no used IDs

    if prefix_ctl == '.':
       prefix = os.path.split(os.getcwd())[1]+'_' # or os.path.basename?
    else:
       prefix = prefix_ctl
    rename_list = make_rename_list(orderedlines, id_regex, prefix, id_prefix, idstart, idstep, idlen )

    now = datetime.datetime.now()
    now_str = now.strftime("%Y_%m_%d_%H_%M_%S")
       
    #now, we have the order file out of the way, let's rename and keep track
    if not is_dry_run:
        orderfile_bak = make_bu_name(orderfile_name, now_str)
        hist_file_name = make_bu_name(history_file, now_str)
        hist_file_obj =  open(hist_file_name, 'a')
        hist_file_obj.write('from, to, %s\n' % now_str)
        
        if is_orderfile:
            try:
                os.rename(orderfile_name, orderfile_bak) 
                hist_file_obj.write(orderfile_name+','+orderfile_bak+'\n')
            except FileNotFoundError:
                notify_user_prob("Orderfile: {0} does not exist".format(path))
                return []
            except PermissionError:
                notify_user_prob("You do not have permissions to rename (back up) {0}".format(path))
                return []
                    
        used_ids = do_rename(rename_list, hist_file_obj) # the real action!
        
        hist_file_obj.close()
        if len(used_ids) ==0:
            # didn't find anything to rename
            os.remove(hist_file_name)
            os.rename(orderfile_bak, orderfile_name)
    else: # dry run, don't worry about "history" at all
        used_ids = do_rename(rename_list, None)
    return used_ids

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
    notify_user_dir('processing dirs: ' + str(dirs_to_process))
    return dirs_to_process

def get_history_filename(history_filename_root:str, dirlist: list[str]):
    """find one (oldest) renaming file (there may be 0..)"""
    (hfr_noext, hfr_ext) = os.path.splitext(history_filename_root)
    dirlist_noext = [os.path.splitext(f)[0] for f in dirlist]
    histfiles = [h for h in dirlist_noext if h.startswith(hfr_noext)]
    if histfiles:
        hf = sorted(histfiles)
        return hf[-1]+hfr_ext # should be oldest
    else:
        notify_user_dir('no history '+ history_filename_root + ' to reverse in '+ os.getcwd())
        return None
  
def undo_rename(curr_name:str, prev_name:str, appender_str:str):
    # if conflict, rename to <to_name>__<appender_str>

    tgt_name = prev_name
    if os.path.exists(prev_name):
        tgt_name += '__' + appender_str
        
    notify_user_file('reverting name '+ curr_name+ '  to '+ tgt_name)
    try:
        os.rename(curr_name, prev_name)
    except FileNotFoundError:
            notify_user_prob("file to revert: {0} does not exist".format(curr_name))
    except:
        notify_user_prob('could not revert ' + curr_name + ' to ' + prev_name)
      
def undo_in_dir(history_filename_root:str, path:str='.',
                keep_rename_history=False, adapt_case:bool=False):
    # change into the dir
    if not change_dir(path):
       return []
    # load the history file
    dirlist = [f for f in os.listdir('.') if os.path.isfile(f)]
    hfilename = get_history_filename(history_filename_root, dirlist)

    
    if hfilename:
        notify_user_dir('using history file '+ hfilename)
        hfile_lines = loadfile_lines(path, hfilename)
        if hfile_lines: # this is the lines for one particular rename
            # process rename actions in reverse order
            appender_str=hfilename.split('__')[-1] # last bit after a double underscore
            for line in reversed(hfile_lines):
                (prev_name, curr_name, *datetime)=line.split(',') # datetime will be empty most lines
                if datetime: # then we have just read in the header
                    break
                else:
                    undo_rename(curr_name, prev_name, appender_str)
        if keep_rename_history:
            os.rename(hfilename, 'u_'+ hfilename)
        else:
            os.remove(hfilename)

@main.command()
def rename(
        startdir:Annotated[str,
        typer.Argument(help='dir to start renaming')]='.',
        
        prefix:Annotated[str,
        typer.Argument(help="prefix for renaming; '.' means use CWD path")]='.',
        
        id_prefix:Annotated[str,
        typer.Argument(help='prefix for new id')]='i',
        
        do_subtree:bool=False,
        
        orderfile:Annotated[str,
        typer.Argument(help='file to look for in each dir holding names in desired order')]='fssort.ini',
        
        history_file:Annotated[str,
        typer.Argument(help='file to track name changes')]='rename_history.csv',
        
        id_per_dir:Annotated[bool,
        typer.Option(help='should ID sequence restart in each dir')]='True',
        
        verbosity:Annotated[int, typer.Option(help='0: mute, 1: probs, 2: per-dir, 3: per-file')]=1,
        
        skip_if_no_orderfile:bool=True,
        id_regex:str=r'\d{2,5}',
        idstart:int=10, idstep:int=10,idlen:int=4,
        dryrun:bool=True
        ): #TODO add in adapt_case param to pass to do_in_folder()
    """rename files to filename/id per ORDERFILE(s); keep HISTORY_FILE(s)"""
  
    # #####  GLOBAL VARS ##### #
    global verbose_level
    verbose_level = verbosity
    global is_dry_run
    is_dry_run = dryrun
    
    idrgx = id_regex
    
    exclude = fetch_ignore('.gfr.ignore')
    
    #TODO as Python-learning, refactor these loops to be cleaenr - maybe w/ lambda and yield?
    dirs_to_process = get_dirs_to_process(startdir, exclude, do_subtree)
    notify_user_dir('processing RENAME in dirs: ' + str(dirs_to_process))

    used_tnames=[]
    next_dir_id_start = idstart
    for dir in dirs_to_process:
        # TODO don't need to keep entire list just last_used
        used_tnames += rename_in_dir(dir,prefix, orderfile, history_file,
                                    id_prefix, id_regex, next_dir_id_start, idstep, idlen,
                                    skip_if_no_orderfile)
        if not id_per_dir and len(used_tnames) > 0:
            last_id_used = get_id_match(used_tnames[-1], id_regex)
            notify_user('continuing ID number sequence after '+ str(last_id_used))
            next_dir_id_start = int(last_id_used) + idstep

@main.command()
def undo(
        startdir:Annotated[str,
        typer.Argument(help='dir to start renaming')]='.',
        
        # do_subtree:Annotated[bool,
        # typer.Argument(help='descend from STARTDIR to subdirs?')]=False,
    
        do_subtree:bool=False,
        
        history_filename_root:Annotated[str,
        typer.Argument(help='case-sensitive beginning of filename listing files to undo')]='rename_history.csv',
        
        verbosity:Annotated[int, typer.Option(help='0: mute, 1: probs, 2: per-dir, 3: per-file')]=1,

        keep_rename_hist:bool=False,
        dryrun:bool=True
    ):
    """undo renaming given in HISTORY_FILE (s)"""
    global verbose_level
    verbose_level = verbosity
    global is_dry_run
    is_dry_run = dryrun
    exclude = fetch_ignore('.gfr.ignore')
    
    dirs_to_process = get_dirs_to_process(startdir, exclude, do_subtree)
    notify_user_dir('processing UNDO in dirs: ' + str(dirs_to_process))
    for dir in dirs_to_process:
        undo_in_dir(history_filename_root, dir, keep_rename_hist)
    
if __name__ == "__main__":
    main()