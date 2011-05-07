
from unittest import TestCase

from pytyp.spec.abcs import *


class NormalizeTest(TestCase):
    
    def assert_normal(self, spec, target):
        result = TSMeta._normalize(spec)
        assert result == target, result 
    
    def test_delayed(self):
        d = Delayed()
        d.set(int)
        self.assert_normal(d, d)
        