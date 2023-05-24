#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Rename files like <dir>/<prefix><ID><suffix>.<ext>
according to ordering file while retaining grouping.

Usage: see --help

NOTE: partly written to force me into learning some Python (3.11),
so apologies if coding sucks/is non-Pythonic (suggestions for improvement?)
"""
import logging

from support import get_dirs_to_process
from support import fetch_ignore
from rename import rename_in_dir
from undo import undo_in_dir

from support import notify_user, notify_user_dir, get_id_match

from support import set_verbosity
from support import set_is_dry_run

from typing_extensions import Annotated
import typer

__author    = "Wayne Stidolph"
__email     = "wayne@stidolph.com"
__license   = "MIT License (see file LICENSE)"
__copyright = "Copyright Wayne Stidolph, 2023"
__status    = "Development"

main=typer.Typer() # for command processing
log=logging.getLogger()

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
    set_verbosity(verbosity)

    set_is_dry_run(dryrun)
    
    idrgx = id_regex
    
    exclude = fetch_ignore('.gfr.ignore')
    
    #TODO as Python-learning, refactor these loops to be cleaenr - maybe w/ lambda and yield?
    dirs_to_process = get_dirs_to_process(startdir, exclude, do_subtree)
    log.info('processing RENAME in dirs: ' + str(dirs_to_process))

    used_tnames=[]
    next_dir_id_start = idstart
    for dir in dirs_to_process:
        # TODO don't need to keep entire list just last_used
        used_tnames += rename_in_dir(dir,prefix, orderfile, history_file,
                                    id_prefix, id_regex, next_dir_id_start, idstep, idlen,
                                    skip_if_no_orderfile)
        if not id_per_dir and len(used_tnames) > 0:
            last_id_used = get_id_match(used_tnames[-1], id_regex)
            log.debug('continuing ID number sequence after '+ str(last_id_used))
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
    set_verbosity(verbosity)

    set_is_dry_run(dryrun)
    exclude = fetch_ignore('.gfr.ignore')
    
    dirs_to_process = get_dirs_to_process(startdir, exclude, do_subtree)
    log.info('processing UNDO in dirs: ' + str(dirs_to_process))
    for dir in dirs_to_process:
        undo_in_dir(history_filename_root, dir, keep_rename_hist)
    
if __name__ == "__main__":
    main()