
from unittest import TestCase

from pytyp import checked


@checked
def str_len(s:str) -> int:
    return len(s)

class Checked():
    
    @checked
    def str_len(self, s:str) -> int:
        return len(s)
    
    @checked
    def bad_len(self, s:str) -> int:
        return 'wrong'


class CheckedTest(TestCase):
    
    def test_function(self):
        assert str_len('abc') == 3
        try:
            str_len([1,2,3])
            assert False, 'Expected error'
        except TypeError:
            pass
    
    def test_method(self):
        c = Checked()
        assert c.str_len('abc') == 3
        try:
            c.str_len([1,2,3])
            assert False, 'Expected error'
        except TypeError:
            pass
        try:
            c.bad_len('abc')
            assert False, 'Expected error'
        except TypeError:
            pass
