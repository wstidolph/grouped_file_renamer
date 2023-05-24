import unittest
import sys
sys.path.append("grouping_renamer") # so modules can import each other
                                    # when run from tests/
import os
import tempfile
from pathlib import Path

import grouping_renamer.undo as undo_mod
import helpers # test support code
    
# Undo testing 
           
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


    def test_get_history_filename(self):
        oldest= 'HF_2021_05_02.csv'
        dlist=['HF.csv', 'HF1.jpg', 'foo.csv', 'HF_2021_05_01.csv', oldest]
        hf_root='HF.csv'
        hf_return=undo_mod.get_history_filename(hf_root, dlist)
        self.assertEqual(hf_return, oldest)

    def test_undo_rename(self):
        "ensure renames happen, and if conflict then rename gets an appended string"
        
        pretend_prev_name="foo"
        orig_file_name='undo_temp_test_file'
        append_str='APPENDED'

        f=open(orig_file_name, 'w') # create file to be renamed
        f.close()
        
        self.assertFalse(os.path.exists(pretend_prev_name))
        self.assertTrue(os.path.exists(orig_file_name))
          
        undo_mod.undo_rename(orig_file_name, pretend_prev_name, append_str)
        
        self.assertFalse(os.path.exists(orig_file_name)) 
        self.assertTrue(os.path.exists(pretend_prev_name))
        
        # remove file, both the reverted and the original names (in case renaming failed)
        self.files_to_cleanup=[pretend_prev_name, orig_file_name]

    def test_undo_rename_appends(self):
        "ensure conflicted rename gets an appended string on rename"
        
        curr_file_name="undo_test_temp_file"
        target_file_name='undo_test_conflicting_file'
        append_str='APPENDED'
        appended_file_name=target_file_name + '__' + append_str
        f=open(curr_file_name, 'w') # create file to be renamed
        f.close()
        f=open(target_file_name, 'w') # create conflict file (the rename target)
        f.close()

        self.assertTrue(os.path.exists(curr_file_name))
        self.assertTrue(os.path.exists(target_file_name)) 
        
        self.assertFalse(os.path.exists(appended_file_name)) # nothing from prev test!
        undo_mod.undo_rename(curr_file_name, target_file_name, append_str)
        
        self.assertFalse(os.path.exists(curr_file_name)) # has been renamed
        self.assertTrue(os.path.exists(appended_file_name))
        self.assertTrue(os.path.exists(target_file_name)) # should be untouched
         
        # remove file, both the reverted and the original names (in case renaming failed)
        self.files_to_cleanup=[curr_file_name, target_file_name, appended_file_name]
    
    def test_undo_rename_if_curr_file_not_exist(self):
        """if the file named does not exist, function should change nothing and emit WARNING log"""
        curr_file='DOES_NOT_EXIST'
        self.assertFalse(os.path.exists(curr_file))
        
        tgt_file='SHOULD_NOT_BE_CREATED'
        self.assertFalse(os.path.exists(curr_file))
        
        expected_log_level=r'WARNING'
        with self.assertLogs('undo', level='WARNING') as lc:
            undo_mod.undo_rename(curr_file, tgt_file)
            self.assertRegexpMatches(lc.output[0], expected_log_level)
            self.assertRegexpMatches(lc.output[0], curr_file)
        
        # nothing should change if the file-to-be-renamed doesn't exist
        self.assertFalse(os.path.exists(curr_file))
        self.assertFalse(os.path.exists(curr_file))
              
    def test_undo_in_dir(self):
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
            undo_mod.undo_in_dir(history_filename_root+'.csv', td, keep_rename_history, adapt_case)
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

    def test_undo_in_dir_if_not_history(self):
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
            undo_mod.undo_in_dir(history_filename_root+'.csv', td, keep_rename_history, adapt_case)
            undone_dlist = os.listdir(td)
            
            # and ensure same entries in dlist and undone_dlist
            self.assertListEqual(dlist, undone_dlist)
        
    def test_undo_in_dir_if_empty_history(self):
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
            undo_mod.undo_in_dir(history_filename_root+'.csv', td, keep_rename_history, adapt_case)
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
        
if __name__ == '__main__':
    unittest.main()