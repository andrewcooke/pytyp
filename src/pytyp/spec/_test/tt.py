
from unittest import TestCase

from pytyp.spec.tt import record


class TypedTupleTest(TestCase):
    
    def test_syntax(self):
#        tt = TypedTuple('Class', a=int, b=str) # unordered
#        tt = TypedTuple('Class', {'a':int, 'b':str}) # quoted
#        tt = TypedTuple('Class')(a=int)(b=str, default='two', access='rw')
#        tt = record('Name', 'a:int,b=6:int', verbose=True, checked=False, private=False, mutable=False)
#        tt = record('Name', 'a:int,b=6:int', verbose=True, checked=False, private=False, mutable=True)
        tt = record('Name', 'a:int,b=6:int', verbose=True, checked=True, mutable=False)
    
    def test_default(self):
        Record = record('Record', 'a:int,b=6:int')
        r = Record(1,2)
        assert r.a == 1, r.a
        assert r['a'] == 1, r['a']
        assert r.b == 2, r.b
        assert r['b'] == 2, r['b']
        try:
            r.a = 3
            assert False, 'Expected immutable'
        except AttributeError:
            pass
        r2 = r._replace(b=3)
        assert r2.b == 3, r2.b
    
    def test_mutable(self):
        Record = record('Record', 'a:int,b=6:int', mutable=True)
        r = Record(1,2)
        assert r.a == 1, r['a']
        assert r.b == 2, r.b
        r['a'] = 3
        r2 = r._replace(b=3)
        assert r2.a == 3, r2.a
        assert r2['a'] == 3, r2['a']
        assert r2.b == 3, r2.b
        try:
            r.c = 4
            assert False, 'Expected error'
        except TypeError:
            pass
        r.a = 'one'
        assert r.a == 'one', r.a

    def test_checked(self):
        Record = record('Record', 'a:int,b=6:int', mutable=True, checked=True)
        r = Record(1,2)
        assert r.a == 1, r['a']
        assert r.b == 2, r.b
        r['a'] = 3
        r2 = r._replace(b=3)
        assert r2.a == 3, r2.a
        assert r2['a'] == 3, r2['a']
        assert r2.b == 3, r2.b
        try:
            r.a = 'one'
            assert False, 'Expected error'
        except TypeError:
            pass
        
    def test_complex(self):
        Record = record('Record', 'a:int,b:Rec(Seq(Opt(int)))', verbose=True)
        