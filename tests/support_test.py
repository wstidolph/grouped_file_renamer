import unittest
import os
import grouping_renamer.support as spt

class TestSupport(unittest.TestCase):
    def test_find_case_insensitive(self):
        """test compare ignores case but the returned list preserves case"""
        ol=['a', 'alibaba']
        dl=['A','b'] # as from a dirlist
        rl=spt.find_case_insensitive(ol, dl)
        self.assertEqual(rl, ['A'])
        
    def test_scrub_dups(self):
        """test that we remove duplicates and blanks, keep others"""
        # verify all-blanks is sane
        dlist = []
        dedup = spt.scrub_dups(dlist)
        self.assertEqual([], dedup)
        
        # verify no-dups returns all orig
        dlist=['a', 'b']
        dedup = spt.scrub_dups(dlist)
        self.assertEqual(dlist, dedup)
        
        # verify dups and '' removed
        dlist=['a', 'b', 'c', 'b', '', 'a']
        dedup = spt.scrub_dups(dlist)
        self.assertEqual(['a', 'b', 'c'], dedup)
        
    def test_remove_any_matching(self):
        # verify no delete if no regex
        dlist=['a', 'b']
        dematch = spt.remove_any_matching(dlist, [])
        self.assertEqual(dlist, dematch)
        
        dlist=['a', 'b']
        dematch = spt.remove_any_matching(dlist, [r'a'])
        self.assertEqual(dematch, ['b'])
        
    def test_scrub_not_matching(self):
        dlist=['a', 'a1', 'b', 'x_i0', 'x_i0010']
        
        # verify get back copy if no must_regex
        snm = spt.scrub_not_matching(dlist,None)
        self.assertEqual(dlist, snm)
        snm = spt.scrub_not_matching(dlist,r'')
        self.assertEqual(dlist, snm)
        
        snm=spt.scrub_not_matching(dlist, r'_i')
        self.assertEqual(snm, ['x_i0','x_i0010'])

    def test_loadfile_lines(self):
        """Test find, opens, reads a line-structured file"""
        folder='tests'
        orderfile='fssort_test.dat' # data includes fssort and FSSORT
        self.assertTrue(os.path.exists(os.path.join(folder, orderfile)))
        return_lines = spt.loadfile_lines(folder, orderfile)
        self.assertGreater(len(return_lines), 3)
    
    def test_id_matching(self):
        """
        ensure id match returns a matched string (id) or None)
        """
        regx = r'\d{2,5}'
        
        idm = spt.get_id_match('a_1965_200_a', regx)
        self.assertEqual(idm, '200')
        
        idm=spt.get_id_match('no_id_exists', regx)
        self.assertIsNone(idm)
        
    def test_fullid(self):
        regx = r'\d{2,5}'
        
        basename='a_long_group_1965_'
        test_id='200'
        idm = spt.get_fullid(basename+test_id, regx)
        self.assertEqual(idm.group(), basename+test_id)
        
        suffix='_a.jpg'
        name_w_suffix = basename+test_id+suffix
        idm = spt.get_fullid(name_w_suffix, regx)
        self.assertEqual(idm.group(), basename+test_id)
        # here's how to get the remainder
        rem_string = name_w_suffix[idm.span()[1]:]
        self.assertEqual(rem_string, suffix)
        
if __name__ == '__main__':
    unittest.main()