import unittest
import sys
sys.path.append("grouping_renamer") # so modules can import each other
                                    # when run from tests/
import os
from pathlib import Path

import grouping_renamer.rename as ren_mod


class TestRename(unittest.TestCase):
    def test_fix_orderlines_adapts_to_case(self):
        olist=['b', 'a', 'X_i0']
        dlist=['a', 'a1', 'b', 'x_i0', 'x_i0010']
        
        adapt_to_case=False
        olf = ren_mod.fix_orderlines(olist, dlist, None, adapt_to_case)
        self.assertEquals(olf, ['b','a'])
        
        adapt_to_case=True
        olf = ren_mod.fix_orderlines(olist, dlist, None, adapt_to_case)
        # with case adapt, X_i0 should match and return x_i0 
        self.assertEquals(olf, ['b','a', 'x_i0'])
                        
    def test_fetch_lists_loads_data(self):
        """
        Test that it can load the ordered names file and the dir listings
        """
        ren_mod.is_dry_run = True # prevent tests from altering files
        ren_mod.verbose_level=2 # set globals
        
        folder='tests'
        orderfile='fssort_test.dat' # data includes fssort and FSSORT
        self.assertTrue(os.path.exists(os.path.join(folder, orderfile)))
    
        # check the ordered file loaded
        adapt_case=True
        (filenames, orderednames) = ren_mod.fetch_lists(folder, orderfile, adapt_case)
        self.assertNotEqual(orderednames, [])
        self.assertIn('fssort_test.dat', orderednames)
        self.assertIn('FSSORT_TEST.DAT', orderednames)
        
        #check the loaded list is sorted
        self.assertEqual('a_first_file',orderednames[0])
        self.assertEqual('z_last_file',orderednames[-1])
        
        # check the directory list loaded
        self.assertNotEqual(filenames, [])
        self.assertIn('fssort_test.dat', filenames)
    
    def test_fetch_lists_adapts_case(self):
        """ test that we find the orderfile if case mismatch on case-sensitive filesys"""
        
        #  not going to try and get the edge cases, just a quick check
        
        ren_mod.is_dry_run = True # prevent tests from altering files
        ren_mod.verbose_level=2 # set globals
        
        folder='tests'
        matched_case='fssort_test.dat' #file should be there in tests dir
        self.assertTrue(os.path.exists(os.path.join(folder, matched_case)))
        
        mismatched_case='FsSort_test.DAT' # this file should *not* be present
        file_found_tho_mismatched = os.path.exists(os.path.join(folder, mismatched_case))

        # only test on a file sys such that the file is *NOT* found if mismatched
        if file_found_tho_mismatched:
            self.skipTest('File System is not case-sensitive so cannot test adapts_case')
        
        # ready to run the tests
        adapt_case=False
        (dirlist, lines_from_mismatched_no_adapt) = ren_mod.fetch_lists(folder, mismatched_case, adapt_case)
        adapt_case=True
        (dirlist, lines_from_mismatched_adapted) = ren_mod.fetch_lists(folder, mismatched_case, adapt_case)
        
        self.assertEqual(lines_from_mismatched_no_adapt, []) # FIXME this would fail on case-insensitive FS
        self.assertNotEqual(lines_from_mismatched_adapted, []) # should load from fssort_test.dat    
        
    def test_make_rename_list(self):
        """
        Test that it makes the replacement list
        """
        orderednames=['a_10.jpg','c_10_a.jpg','a_10_a.jpg']
        to_prefix='b_1965'
        id_prefix = '_i'
        id_regex = r'\d{2,5}'
        id_start=10
        id_len=4
        id_step=4
        expected=[{'from':orderednames[0], 'to':'b_1965_i0010.jpg'},
            {'from':orderednames[2], 'to':'b_1965_i0010_a.jpg'},
            {'from':orderednames[1], 'to':'b_1965_i0014_a.jpg'}
            ]
        
        rd = ren_mod.make_rename_list(orderednames.copy(),id_regex,
                                 to_prefix, id_prefix,
                                 id_start,id_step,id_len)
        self.assertEqual(rd[0]['from'], expected[0]['from'])
        self.assertEqual(rd[0]['to'], expected[0]['to'])
        self.assertEqual(rd[1]['from'], expected[1]['from'])
        self.assertEqual(rd[1]['to'], expected[1]['to'])
        self.assertEqual(rd[2]['from'], expected[2]['from'])
        self.assertEqual(rd[2]['to'], expected[2]['to'])

if __name__ == '__main__':
    unittest.main()