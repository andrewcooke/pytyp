
from unittest import TestCase

from pytyp.spec.tt import record


class TypedTupleTest(TestCase):
    
    def test_syntax(self):
#        tt = TypedTuple('Class', a=int, b=str) # unordered
#        tt = TypedTuple('Class', {'a':int, 'b':str}) # quoted
#        tt = TypedTuple('Class')(a=int)(b=str, default='two', access='rw')
        #tt = record('Name', 'a:int,b=6:int', verbose=True, checked=False, private=False, mutable=False)
        #tt = record('Name', 'a:int,b=6:int', verbose=True, checked=False, private=False, mutable=True)
        tt = record('Name', 'a:int,b=6:int', verbose=True, checked=True, private=False, mutable=False)
        