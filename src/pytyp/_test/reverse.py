
from unittest import TestCase
from inspect import formatargspec, getfullargspec

from pytyp._test.support import SimpleArgs, TypedArgs, NamedArgs


class ReverseTest(TestCase):
    
    def test_argspec(self):
        spec = getfullargspec(TypedArgs.__init__)
        s = formatargspec(*spec)
        assert s == '(self, x: pytyp._test.support.NamedArgs, y: pytyp._test.support.SimpleArgs=None) -> int', s
        ann = spec.annotations
        assert 'x' in ann, ann
        assert ann['x'] == NamedArgs
        assert 'y' in ann, ann
        assert ann['y'] == SimpleArgs
        assert 'return' in ann, ann
        assert ann['return'] == int
        assert len(ann) == 3


def mustbe(n):
    def decorator(f):
        def wrapper(self, x):
            if x != n:
                raise ValueError
            return f(self, x)
        return wrapper
    return decorator


class Decorated():
    
    @mustbe(2)
    def __init__(self, value):
        self.value = value
        

class DecoratorTest(TestCase):
    
    def test_decorator(self):
        d = Decorated(2)
        assert d.value == 2
        try:
            Decorated(1)
            assert False, 'Expected error'
        except ValueError:
            pass
        