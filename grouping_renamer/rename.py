import os
import datetime
from typing import List

from support import change_dir,fetch_lists,loadfile_lines
from support import find_case_insensitive, remove_any_matching, scrub_dups, scrub_not_matching
from support import get_fullid,get_next_id
# notify* should move to loggin calls
from support import notify_user,notify_user_file,notify_user_dir, notify_user_prob
from support import get_is_dry_run

def make_bu_name(fn: str, bustr: str):
    """add backup-indication string (bustr) to the fn without change file extension"""
    ld=fn.rfind('.')
    if(ld <0): # no dot at all
        return fn+'__'+bustr
    else:
        return fn[:ld]+'__'+bustr+fn[ld:]

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
            notify_user_file('renaming: '+ fname + ' to '+ tname)
            used_newnames.append(tname)
            if not get_is_dry_run():
                os.rename(fname, tname)
                hist_file_obj.write(fname+','+tname+'\n')
    notify_user_dir('dir '+os.getcwd()+' renamed '+ str(len(used_newnames)) + ' files')
    return used_newnames
                    
def rename_in_dir(path, prefix_ctl,
                 orderfile_name, history_file,
                 id_prefix, id_regex, idstart, idstep, idlen,
                 skip_if_no_orderfile,
                 adapt_case=True) -> list[str]:
    """execute renaming in a single folder"""
    notify_user('do_in_folder ' + path)
    if not change_dir(path): # TODO change to pass path, not changing directory
       return []

    is_orderfile = os.path.isfile(orderfile_name)
    if (not is_orderfile or not os.access(orderfile_name, os.R_OK)) and skip_if_no_orderfile:
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
    if not get_is_dry_run():
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
