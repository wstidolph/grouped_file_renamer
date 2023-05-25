import unittest
import sys
sys.path.append("grouping_renamer") # so modules can import each other
                                    # when run from tests/
import os
import tempfile
from pathlib import Path

#import grouping_renamer.undo as undo_mod
from grouping_renamer import undo
import grouping_renamer.support as spt_mod
from unittest import mock

import helpers # test support code
    
# Undo testing 
# turn off dry_run flag so we can actually write to the temp dirs
# rather than just mocking, because I want to see how the file system
# affects the test ... a bit more of an "integration" test, I suppose
@mock.patch('grouping_renamer.undo.get_is_dry_run', return_value=False)           
class TestUndo(unittest.TestCase):
    files_to_cleanup = []
    
    def setUp(self):
        self.files_to_cleanup = []
    
    def tearDown(self):
        for f in self.files_to_cleanup:
            try:
                os.remove(f)
            except:
                pass

    def test_get_history_filename(self, mock_dr):
        oldest= 'HF_2021_05_02.csv'
        dlist=['HF.csv', 'HF1.jpg', 'foo.csv', 'HF_2021_05_01.csv', oldest]
        hf_root='HF.csv'
        hf_return=undo.get_history_filename(hf_root, dlist)
        self.assertEqual(hf_return, oldest)

    def test_undo_rename(self, mock_dr):
        "ensure renames happen, and if conflict then rename gets an appended string"
        with tempfile.TemporaryDirectory() as td:
            prev_name=os.path.join(td,'foo')
            curr_file_name=os.path.join(td,'undo_temp_test_file')
            append_str='APPENDED'

            f=open(curr_file_name, 'w') # create file to be renamed
            f.close()
            
            self.assertFalse(os.path.exists(prev_name))
            self.assertTrue(os.path.exists(curr_file_name))
            
            undo.undo_rename(curr_file_name, prev_name, append_str)
            
            self.assertFalse(os.path.exists(curr_file_name)) # file has been renamed
            self.assertTrue(os.path.exists(prev_name))
            
            # remove file, both the reverted and the original names (in case renaming failed)
            # self.files_to_cleanup=[prev_name, curr_file_name] # don't really need to in a temp dir

    def test_undo_rename_appends(self, mock_dr):
        "ensure conflicted rename gets an appended string on rename"
        with tempfile.TemporaryDirectory() as td:        
            curr_file_name=os.path.join(td, 'undo_test_temp_file')
            target_file_name=os.path.join(td, 'undo_test_conflicting_file')
            append_str='APPENDED'
            appended_file_name=target_file_name + '__' + append_str
            f=open(curr_file_name, 'w') # create file to be renamed
            f.close()
            f=open(target_file_name, 'w') # create conflict file (the rename target)
            f.close()

            self.assertTrue(os.path.exists(curr_file_name))
            self.assertTrue(os.path.exists(target_file_name))
            self.assertFalse(os.path.exists(appended_file_name))
            
            undo.undo_rename(curr_file_name, target_file_name, append_str)
            
            self.assertFalse(os.path.exists(curr_file_name)) # has been renamed
            self.assertTrue(os.path.exists(target_file_name)) # should be untouched
            self.assertTrue(os.path.exists(appended_file_name)) # renamed
         
        # remove file, both the reverted and the original names (in case renaming failed)
        # self.files_to_cleanup=[curr_file_name, target_file_name, appended_file_name]
    
    def test_undo_rename_if_curr_file_not_exist(self, mock_dr):
        """if the file named does not exist, function should change nothing and emit WARNING log"""
        with tempfile.TemporaryDirectory() as td:
            curr_file=os.path.join(td, 'DOES_NOT_EXIST')
            self.assertFalse(os.path.exists(curr_file))
            
            tgt_file=os.path.join(td,'SHOULD_NOT_BE_CREATED')
            self.assertFalse(os.path.exists(tgt_file))
            
            expected_log_level=r'WARNING'
            with self.assertLogs('undo', level='WARNING') as lc:
                undo.undo_rename(curr_file, tgt_file) #
                self.assertRegexpMatches(lc.output[0], expected_log_level)
                self.assertRegexpMatches(lc.output[0], curr_file)
            
            # nothing should change if the file-to-be-renamed doesn't exist
            self.assertFalse(os.path.exists(curr_file))
            self.assertFalse(os.path.exists(tgt_file))
              
    def test_undo_in_dir(self, mock_dr):
        """ensure files in history CSV are renamed, othr files are not, and the history file is removed"""
        with tempfile.TemporaryDirectory() as td:
            history_filename_root="hf"
            keep_rename_history=False
            adapt_case=False
            num_files=3
            unchanging_files=['SHOULD_NOT_CHANGE.jpg', 'silly.JPG', 'a']
            #make files in the directory, including 'hf_<some_date>.csv'
            helpers.h_create_rename_files(td, history_filename_root, unchanging_files, num_files)
            dlist=os.listdir(td)
            self.assertNotEqual(dlist, []) # there must be at *least* the history file!
            
            # the undo_in_dir should rename files and remove the history file
            undo.undo_in_dir(history_filename_root+'.csv', td, keep_rename_history, adapt_case)
            dlist=os.listdir(td)

            # all files starting with 'A_' should now end with '_old'
            ends_with_old = r'_old.jpg$'
            A_files = [f for f in dlist if f.startswith('A_')]
            for a in A_files:
                self.assertRegexpMatches(a, ends_with_old)
                
            # non-rename files should not change
            other_f = [f for f in dlist if not f.startswith('A_')]
            for uf in unchanging_files:
                self.assertIn(uf, other_f)
                
            # history file file should be removed
            hflist = [f for f in dlist if f.startswith(history_filename_root)]
            self.assertEqual(hflist, [])

    def test_undo_in_dir_if_not_history(self, mock_dr):
        """ensure a directory with no history file is left unchanged"""
        with tempfile.TemporaryDirectory() as td:
            history_filename_root="hf"
            keep_rename_history=False
            adapt_case=False
            num_files=3
            unchanging_files=['SHOULD_NOT_CHANGE.jpg', 'silly.JPG', 'a']
            #make files in the directory, including 'hf_<some_date>.csv'
            helpers.h_create_rename_files(td, history_filename_root, unchanging_files, num_files)
            dlist=os.listdir(td)
            
            hf = [f for f in dlist if f.startswith(history_filename_root)]
            for h in hf:
                os.remove(os.path.join(td, h))
            # OK, we have files but no history; let's update the dlist
            dlist=os.listdir(td)
            
            # invoke the undo
            undo.undo_in_dir(history_filename_root+'.csv', td, keep_rename_history, adapt_case)
            undone_dlist = os.listdir(td)
            
            # and ensure same entries in dlist and undone_dlist
            self.assertListEqual(dlist, undone_dlist)
        
    def test_undo_in_dir_if_empty_history(self, mock_dr):
        with tempfile.TemporaryDirectory() as td:
            history_filename_root="hf"
            keep_rename_history=False
            adapt_case=False
            num_files=0
            unchanging_files=['SHOULD_NOT_CHANGE.jpg', 'silly.JPG', 'a']
            #make files in the directory, including 'hf_<some_date>.csv'
            helpers.h_create_rename_files(td, history_filename_root, unchanging_files, num_files)
            dlist=os.listdir(td)
            self.assertNotEqual(dlist, []) # there must be at *least* the history file!
            
            A_orig_files = [f for f in dlist if f.startswith('A_')]
            # the undo_in_dir should rename files and remove the history file
            undo.undo_in_dir(history_filename_root+'.csv', td, keep_rename_history, adapt_case)
            dlist=os.listdir(td)

            A_after_files = [f for f in dlist if f.startswith('A_')]
            self.assertEqual(A_orig_files, A_after_files)
                
            # non-rename files should not change
            other_f = [f for f in dlist if not f.startswith('A_')]
            for uf in unchanging_files:
                self.assertIn(uf, other_f)
                
            # and history file file should be removed
            hflist = [f for f in dlist if f.startswith(history_filename_root)]
            self.assertEqual(hflist, [])

    def test_undo_in_dir_respects_dryrun(self, mock_dr):
         """undo_in_dir respects the flag (doesn't rename or delete history files)"""
         # set up a directory with a history file
         with tempfile.TemporaryDirectory() as td:
            history_filename_root="hf"
            keep_rename_history=False
            adapt_case=False
            #make files in the directory, including 'hf_<some_date>.csv'
            helpers.h_create_rename_files(td)
            
            dlist=os.listdir(td)
            hflist = [f for f in dlist if f.startswith(history_filename_root)]
            self.assertNotEqual(hflist, []) # there must be at *least* the history file!
            
         # execute the undo_in_dir with dryrun on, check no hange to history file
            mock_dr.return_value=True
            undo.undo_in_dir(history_filename_root+'.csv', td, keep_rename_history, adapt_case)
            dlist=os.listdir(td)
            hflist_new = [f for f in dlist if f.startswith(history_filename_root)]
            self.assertEqual(hflist_new, hflist)
             
         # execute the undo with dryrun off
            mock_dr.return_value=False
            undo.undo_in_dir(history_filename_root+'.csv', td, keep_rename_history, adapt_case)
            dlist=os.listdir(td)
            hflist_new = [f for f in dlist if f.startswith(history_filename_root)]
            
            hf_gone = (hflist_new == []) or hflist[0].startswith('u_')
            self.assertTrue(hf_gone) # there must be at *least* the history file!
         
    def test_undo_rename_respects_dryrun(self, mock_dr):
        """verify undo_rename() respects the flag, doesn't update actual files"""
        # rather than asserting os.rename isn't called, lets watch for real effect
        # since maybe the file name interacts with the renaming?
        # slower but that's OK for me
        # ensure there is one real file to rename
        with tempfile.TemporaryDirectory() as td:
            dummy_abs = os.path.join(td, 'DUMMY')
            rename_tgt_abs = os.path.join(td, 'RENAMED')
            f = open(dummy_abs, 'w')
            f.close()
            self.assertTrue(os.path.exists(dummy_abs))
            self.assertFalse(os.path.exists(rename_tgt_abs))
            
            # with dryrun on, no change
            mock_dr.return_value=True
            undo.undo_rename(dummy_abs, rename_tgt_abs)
            self.assertTrue(os.path.exists(dummy_abs))
            self.assertFalse(os.path.exists(rename_tgt_abs))
            
            # with dryrun off, changed name
            mock_dr.return_value=False
            undo.undo_rename(dummy_abs, rename_tgt_abs)
            self.assertFalse(os.path.exists(dummy_abs))
            self.assertTrue(os.path.exists(rename_tgt_abs))
if __name__ == '__main__':
    unittest.main()