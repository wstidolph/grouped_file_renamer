import unittest
import os
from pathlib import Path

from grouping_renamer import gfr

class TestRename(unittest.TestCase):
    def test_find_case_insensitive(self):
        """test compare ignores case but the returned list preserves case"""
        ol=['a', 'alibaba']
        dl=['A','b'] # as from a dirlist
        rl=gfr.find_case_insensitive(ol, dl)
        self.assertEquals(rl, ['A'])
        
    def test_scrub_dups(self):
        """test that we remove duplicates and blanks, keep others"""
        # verify all-blanks is sane
        dlist = []
        dedup = gfr.scrub_dups(dlist)
        self.assertEqual([], dedup)
        
        # verify no-dups returns all orig
        dlist=['a', 'b']
        dedup = gfr.scrub_dups(dlist)
        self.assertEqual(dlist, dedup)
        
        # verify dups and '' removed
        dlist=['a', 'b', 'c', 'b', '', 'a']
        dedup = gfr.scrub_dups(dlist)
        self.assertEqual(['a', 'b', 'c'], dedup)
        
    def test_remove_any_matching(self):
        # verify no delete if no regex
        dlist=['a', 'b']
        dematch = gfr.remove_any_matching(dlist, [])
        self.assertEqual(dlist, dematch)
        
        dlist=['a', 'b']
        dematch = gfr.remove_any_matching(dlist, [r'a'])
        self.assertEqual(dematch, ['b'])
        
    def test_scrub_not_matching(self):
        dlist=['a', 'a1', 'b', 'x_i0', 'x_i0010']
        
        # verify get back copy if no must_regex
        snm = gfr.scrub_not_matching(dlist,None)
        self.assertEquals(dlist, snm)
        snm = gfr.scrub_not_matching(dlist,r'')
        self.assertEquals(dlist, snm)
        
        snm=gfr.scrub_not_matching(dlist, r'_i')
        self.assertEquals(snm, ['x_i0','x_i0010'])

    def test_loadfile_lines(self):
        """Test find, opens, reads a line-structured file"""
        folder='tests'
        orderfile='fssort_test.dat' # data includes fssort and FSSORT
        self.assertTrue(os.path.exists(os.path.join(folder, orderfile)))
        return_lines = gfr.loadfile_lines(folder, orderfile)
        self.assertGreater(len(return_lines), 3)
        
    def test_fix_orderlines_adapts_to_case(self):
        olist=['b', 'a', 'X_i0']
        dlist=['a', 'a1', 'b', 'x_i0', 'x_i0010']
        
        adapt_to_case=False
        olf = gfr.fix_orderlines(olist, dlist, None, adapt_to_case)
        self.assertEquals(olf, ['b','a'])
        
        adapt_to_case=True
        olf = gfr.fix_orderlines(olist, dlist, None, adapt_to_case)
        # with case adapt, X_i0 should match and return x_i0 
        self.assertEquals(olf, ['b','a', 'x_i0'])
                        
    def test_fetch_lists_loads_data(self):
        """
        Test that it can load the ordered names file and the dir listings
        """
        gfr.is_dry_run = True # prevent tests from altering files
        gfr.verbose_level=2 # set globals
        
        folder='tests'
        orderfile='fssort_test.dat' # data includes fssort and FSSORT
        self.assertTrue(os.path.exists(os.path.join(folder, orderfile)))
    
        # check the ordered file loaded
        adapt_case=True
        (filenames, orderednames) = gfr.fetch_lists(folder, orderfile, adapt_case)
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
        
        gfr.is_dry_run = True # prevent tests from altering files
        gfr.verbose_level=2 # set globals
        
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
        (dirlist, lines_from_mismatched_no_adapt) = gfr.fetch_lists(folder, mismatched_case, adapt_case)
        adapt_case=True
        (dirlist, lines_from_mismatched_adapted) = gfr.fetch_lists(folder, mismatched_case, adapt_case)
        
        self.assertEqual(lines_from_mismatched_no_adapt, []) # FIXME this would fail on case-insensitive FS
        self.assertNotEqual(lines_from_mismatched_adapted, []) # should load from fssort_test.dat
        
    def test_id_matching(self):
        """
        ensure id match returns a matched string (id) or None)
        """
        regx = r'\d{2,5}'
        
        idm = gfr.get_id_match('a_1965_200_a', regx)
        self.assertEqual(idm, '200')
        
        idm=gfr.get_id_match('no_id_exists', regx)
        self.assertIsNone(idm)
        
    def test_fullid(self):
        regx = r'\d{2,5}'
        
        basename='a_long_group_1965_'
        test_id='200'
        idm = gfr.get_fullid(basename+test_id, regx)
        self.assertEqual(idm.group(), basename+test_id)
        
        suffix='_a.jpg'
        name_w_suffix = basename+test_id+suffix
        idm = gfr.get_fullid(name_w_suffix, regx)
        self.assertEqual(idm.group(), basename+test_id)
        # here's how to get the remainder
        rem_string = name_w_suffix[idm.span()[1]:]
        self.assertEqual(rem_string, suffix)
        
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
        
        rd = gfr.make_rename_list(orderednames.copy(),id_regex,
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