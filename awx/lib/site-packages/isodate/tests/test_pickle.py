import unittest
import cPickle as pickle
import isodate


class TestPickle(unittest.TestCase):
    '''
    A test case template to parse an ISO datetime string into a
    datetime object.
    '''

    def test_pickle(self):
        '''
        Parse an ISO datetime string and compare it to the expected value.
        '''
        dti = isodate.parse_datetime('2012-10-26T09:33+00:00')
        pikl = pickle.dumps(dti, 2)
        dto = pickle.loads(pikl)
        self.assertEqual(dti, dto)


def test_suite():
    '''
    Construct a TestSuite instance for all test cases.
    '''
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPickle))
    return suite

# load_tests Protocol
def load_tests(loader, tests, pattern):
    return test_suite()

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
