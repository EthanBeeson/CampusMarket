import unittest

class TestSimpleStuff(unittest.TestCase):
    
    def test_true_is_true(self):
        self.assertTrue(True)
    
    def test_math_still_works(self):
        self.assertEqual(2 + 2, 4)

if __name__ == '__main__':
    unittest.main()