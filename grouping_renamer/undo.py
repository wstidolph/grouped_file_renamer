import os
import logging

from support import change_dir,loadfile_lines

log=logging.getLogger('undo')

def get_history_filename(history_filename_root:str, dirlist: list[str]):
    """find one (oldest) renaming file (there may be 0..)"""
    (hfr_noext, hfr_ext) = os.path.splitext(history_filename_root)
    dirlist_noext = [os.path.splitext(f)[0] for f in dirlist]
    histfiles = [h for h in dirlist_noext if h.startswith(hfr_noext)]
    if histfiles:
        hf = sorted(histfiles)
        return hf[-1] + hfr_ext # should be oldest
    else:
        log.warning('no history '+ history_filename_root + ' to reverse in '+ os.getcwd())
        return None
  
def undo_rename(curr_name:str, prev_name:str, appender_str:str):
    # if conflict, rename to <to_name>__<appender_str>

    tgt_name = prev_name
    if os.path.exists(prev_name):
        tgt_name += '__' + appender_str
        
    log.debug('reverting name '+ curr_name+ '  to '+ tgt_name)
    try:
        os.rename(curr_name, prev_name)
    except FileNotFoundError:
        log.warning("file to revert: {0} (from history) does not exist".format(curr_name))
    except:
        log.warning('could not revert ' + curr_name + ' to ' + prev_name)
      
def undo_in_dir(history_filename_root:str, path:str='.',
                keep_rename_history=False, adapt_case:bool=False):
    # change into the dir
    if not change_dir(path):
       return []
    # load the history file
    dirlist = [f for f in os.listdir('.') if os.path.isfile(f)]
    hfilename = get_history_filename(history_filename_root, dirlist)

    if hfilename:
        log.info('using history file '+ hfilename)
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