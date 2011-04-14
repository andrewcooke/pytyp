
from unittest import TestCase

from pytyp.spec.base import *


class NormalizeTest(TestCase):
    
    def assert_normal(self, spec, target):
        result = normalize(spec)
        assert result == target, result 
    
    def test_delayed(self):
        d = Delayed()
        d += int
        self.assert_normal(d, Cls(int))
        