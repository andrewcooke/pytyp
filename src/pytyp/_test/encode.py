
from unittest import TestCase

from pytyp._test.support import SimpleArgs
from pytyp import encode


class EncodeTest(TestCase):
    
    def test_circular(self):
        s = SimpleArgs(1,2,3)
        s.a = s
        try:
            encode(s)
            assert False, 'Expected error'
        except ValueError as e:
            assert 'Circular' in str(e), e
            