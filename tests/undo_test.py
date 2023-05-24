import unittest
import sys
sys.path.append("grouping_renamer") # so modules can import each other
                                    # when run from tests/
import os
import tempfile
from pathlib import Path

import grouping_renamer.undo as undo_mod

# Undo testing 

class TestUndo(unittest.TestCase):
    
    def test_this_file_loads(self):
        self.assertTrue(True)

    def test_get_history_filename(self):
        oldest= 'HF_2021_05_02.csv'
        dlist=['HF.csv', 'HF1.jpg', 'foo.csv', 'HF_2021_05_01.csv', oldest]
        hf_root='HF.csv'
        hf_return=undo_mod.get_history_filename(hf_root, dlist)
        self.assertEqual(hf_return, oldest)

    def test_undo_rename(self):
        "ensure renames happen, and if conflict then rename gets an appneded string"
        orig_file_name='undo_temp_test_file'
        with open(orig_file_name,'w') as tmpfile:
            pretend_prev_name="foo"
            undo_mod.undo_rename(orig_file_name, pretend_prev_name, "__APPENDED")
            reverted_name=os.path.basename(tmpfile)
            self.assertEqual(pretend_prev_name,reverted_name)
    
if __name__ == '__main__':
    unittest.main()