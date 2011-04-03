
from unittest import TestCase
from pytyp import validate, Opt
from pytyp._test.support import SimpleArgs
from collections import namedtuple


class ValidateTest(TestCase):
    
    def test_direct(self):
        validate(str, 'a')
        validate(int, 1)
        validate(list, [1,2])
        validate(dict, {1:2})
        validate(object, object())
        validate(SimpleArgs, SimpleArgs(1,2,3))
        
    def assert_error(self, trigger):
        try:
            trigger()
            assert False, 'Expected error'
        except TypeError:
            pass
        
    def test_direct_fail(self):
        self.assert_error(lambda: validate(str, 1))
        self.assert_error(lambda:validate(int, [1,2]))
        self.assert_error(lambda:validate(list, {1:2}))
        self.assert_error(lambda:validate(dict, object()))
        validate(object, SimpleArgs(1,2,3)) # inclusional
        self.assert_error(lambda:validate(SimpleArgs, 'a'))
    
    def test_polymorphic_none(self):
        validate(None, 'a')
        validate(None, 1)
        validate(None, [1,2])
        validate(None, {1:2})
        validate(None, object())
        validate(None, SimpleArgs(1,2,3))
    
    def test_maybe(self):
        validate(Opt(str), None)
        validate(Opt(int), None)
        validate(Opt(list), None)
        validate(Opt(dict), None)
        validate(Opt(object), None)
        validate(Opt(SimpleArgs), None)
    
    def test_polymorphic_list(self):
        validate([int], [1,2,3])
        validate([int], [])
        validate([Opt(int)], [1,None,3])
        validate(None, [1,2,3])
        validate([None], [1,2,3])
        self.assert_error(lambda: validate([int], [1,'two',3]))
        self.assert_error(lambda: validate([], [1,2,3]))
        self.assert_error(lambda: validate([int,str], [1,'two']))
        
    def test_product_as_tuple(self):
        validate((int,), [1])
    
    def test_product_tuple(self):
        validate((int, str), (1, 'a'))
        self.assert_error(lambda: validate((int, str), ('a', 1)))
        NT = namedtuple('NT', 'a, b')
        validate(NT(int, str), NT(1, 'a'))
        self.assert_error(lambda: validate(NT(int, str), NT('a', 1)))
        validate(NT(int, str), NT(a=1, b='a'))
        validate(NT(a=int, b=str), NT(b='a', a=1))
        self.assert_error(lambda: validate(NT(int, str), NT(a='a', b=1)))
        