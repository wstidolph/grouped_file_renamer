import unittest
import sys
sys.path.append("grouping_renamer") # so modules can import each other
                                    # when run from tests/
import os
from pathlib import Path

# Undo testing 

class TestUndo(unittest.TestCase):
    
    def test_this_file_loads(self):
        self.assertTrue(True)
        

if __name__ == '__main__':
    unittest.main()